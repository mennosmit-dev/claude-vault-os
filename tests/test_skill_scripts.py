import io
import json
from datetime import date, timedelta

import pytest
from conftest import ROOT, load

SKILLS = ROOT / ".claude" / "skills"
render = load("chief_render", SKILLS / "chief" / "render.py")
qr = load("question_round", SKILLS / "question-round" / "scripts" / "question_round.py")
brief = load("brief_html", SKILLS / "brief" / "brief_html.py")


# --- chief: week logic -------------------------------------------------------


@pytest.mark.parametrize(
    ("today", "monday"),
    [
        (date(2026, 11, 9), date(2026, 11, 9)),  # Monday: this week
        (date(2026, 11, 12), date(2026, 11, 9)),  # Thursday: still this week
        (date(2026, 11, 13), date(2026, 11, 16)),  # Friday: the coming week
        (date(2026, 11, 15), date(2026, 11, 16)),  # Sunday
    ],
)
def test_work_week(today, monday):
    assert render.work_week(today) == monday


def test_week_deadline_keeps_a_date_inside_the_week():
    monday = date(2026, 11, 16)
    assert render.week_deadline("- [ ] a  [due:: 2026-11-17]", monday) == "- [ ] a  [due:: 2026-11-17]"
    assert render.week_deadline("- [ ] a  [due:: 2026-12-01]", monday) == "- [ ] a  [due:: 2026-11-20]"
    assert render.week_deadline("- [ ] a", monday) == "- [ ] a  [due:: 2026-11-20]"


def test_set_field_replaces_and_removes():
    line = "- [ ] a  [due:: 2026-01-01]  [prio:: high]"
    assert render.set_field(line, "due", "2026-02-02") == "- [ ] a  [prio:: high]  [due:: 2026-02-02]"
    assert render.set_field(line, "due", "") == "- [ ] a  [prio:: high]"


# --- chief: parsing and applying /chief tasks --------------------------------


@pytest.fixture
def chief_vault(tmp_path, monkeypatch):
    state = tmp_path / ".claude" / "state"
    monkeypatch.setattr(render, "VAULT", tmp_path)
    monkeypatch.setattr(render, "CARDS_STATE", state / "chief-tasks.json")
    monkeypatch.setattr(render, "WEEK_STATE", state / "next-week.json")
    monkeypatch.setattr(render, "ME", "me")
    p = tmp_path / "Alpha"
    p.mkdir()
    (p / "tasks.md").write_text(
        "## Doing\n\n## This week\n"
        "- [ ] Write eval set  [due:: 2020-01-01]  [prio:: high]\n"
        "- [ ] Send data  [owner:: Ravi]\n"
        "\n## Backlog\n- [ ] Old idea\n\n## Done\n- [x] Setup  [done:: 2020-01-01]\n",
        encoding="utf-8",
    )
    (tmp_path / "_system").mkdir()  # underscore folders are never projects
    return tmp_path


def test_parse_reads_sections_and_fields(chief_vault):
    tasks = render.parse(chief_vault / "Alpha")
    assert [t["title"] for t in tasks] == ["Write eval set", "Send data", "Old idea", "Setup"]
    assert tasks[0]["section"] == "This week" and tasks[0]["fields"]["prio"] == "high"
    assert tasks[3]["done"] is True
    assert render.is_mine(tasks[0]) and not render.is_mine(tasks[1])


def test_cards_then_apply_moves_lines(chief_vault, monkeypatch, capsys):
    render.cards(type("A", (), {"project": None})())
    payload = json.loads(capsys.readouterr().out)
    ids = {q["q"]: q["id"] for q in payload["questions"]}
    assert payload["questions"][0]["q"] == "Write eval set"  # overdue first

    answers = {ids["Write eval set"]: "today", ids["Old idea"]: "drop", ids["Send data"]: "done"}
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(answers)))
    render.apply(None)

    text = (chief_vault / "Alpha" / "tasks.md").read_text(encoding="utf-8")
    today = date.today().isoformat()
    doing = text.split("## This week")[0]
    assert f"- [ ] Write eval set  [prio:: high]  [due:: {today}]" in doing
    assert "Old idea" not in text
    assert f"- [x] Send data  [owner:: Ravi]  [done:: {today}]" in text.split("## Done")[1]


def test_roll_over_moves_next_week_into_this_week(chief_vault):
    tasks = chief_vault / "Alpha" / "tasks.md"
    tasks.write_text("## This week\n\n## Next week\n- [ ] later thing\n\n## Done\n", encoding="utf-8")
    render.WEEK_STATE.parent.mkdir(parents=True, exist_ok=True)
    past_monday = render.work_week(date.today()) - timedelta(days=7)
    render.WEEK_STATE.write_text(json.dumps({"monday": past_monday.isoformat()}), encoding="utf-8")
    render.roll_over(date.today())
    text = tasks.read_text(encoding="utf-8")
    assert text.index("later thing") < text.index("## Next week")
    assert not render.WEEK_STATE.exists()


# --- question round: input validation ----------------------------------------


def test_validate_applies_batch_options():
    qs, skip = qr.validate_questions(
        {"options": ["keep", "drop"], "skip": "leave", "questions": [{"id": "a", "q": "A?"}]}
    )
    assert qs == [{"id": "a", "q": "A?", "options": ["keep", "drop"]}]
    assert skip == "leave"


def test_validate_defaults_to_yes_no():
    qs, _ = qr.validate_questions([{"id": "a", "q": "A?"}])
    assert qs[0]["options"] == ["yes", "no"]


@pytest.mark.parametrize(
    "raw",
    [
        [],
        [{"id": "a", "q": "A?"}, {"id": "a", "q": "B?"}],  # duplicate id
        [{"id": "a", "q": ""}],
        [{"id": "a", "q": "A?", "options": ["only one"]}],
        [{"id": "a", "q": "A?", "options": [str(i) for i in range(10)]}],
        "not a list",
    ],
)
def test_validate_rejects_bad_input(raw):
    with pytest.raises(ValueError):
        qr.validate_questions(raw)


# --- brief: markdown to html -------------------------------------------------


def test_brief_short_label_for_dated_notes():
    assert brief.short_label("2026-09-30 - Call - Data owner - kickoff", "") == "Call Data owner, 30 Sep"
    assert brief.short_label("Anything", "custom") == "custom"


def test_brief_render_writes_export(tmp_path):
    md = tmp_path / "Demo" / "Brief - Ravi - 2026-11-12.md"
    md.parent.mkdir()
    md.write_text(
        '---\ntype: brief\ndate: 2026-11-12\nsummary: "Kickoff"\n---\n# Brief - Ravi\n'
        "## Goal\n- Agree on the data cut\n## Questions and points\n1. Which months?\n"
        "## Open actions\n- Ravi: send the export\n- Budget is not known\n",
        encoding="utf-8",
    )
    out = brief.render(md)
    html = out.read_text(encoding="utf-8")
    assert out == md.parent / "_export" / "Brief - Ravi - 2026-11-12.html"
    assert "Agree on the data cut" in html and '<span class="who">Ravi</span>' in html
    assert '<span class="nk">not known</span>' in html
