# Example structure: an evaluation write-up

Skeleton of a write-up that worked well (an experiment over several versions, written for colleagues). Placeholders in angle brackets.

```markdown
# <Topic>: where are we and what next?
From <baseline> to <latest version>

## The short version
<2 to 4 sentences: it delivered something, and it is not solved. The main improvement, then the limit you hit.>

- Version 0 had <setup>. <What already worked and why you left it out of the measurement.> For the hard group, accuracy started around <x>%.
- Version 1 added <change>. Accuracy rose to about <y>% (+<y-x> points).
- Version 2 added <change>. <What it gave, and what it does not prove.>
- Version 3 added a real regression test (<kinds of tests>). It confirmed <finding>.
- Version 4 was mixed. <What improved>, <what stayed wrong>.

**What I conclude.** <The headline number.> <What seems to work best.> It is not a fixed rule: <counter-example>. The next step is <controlled cycle with a human approving changes>.

### What to keep in mind
- <Concrete guideline 1.>
- <Distinctions to make when measuring.>

### Items that stay hard
| Item | Current state |
|---|---|
| <item> | <how it still fails> |

### Proposal
<One sentence on where the value is.>

1. **Collect:** <step>.
2. **Compare:** <step>.
3. **Review:** <who approves, how often>.
```

What makes it work:
- Conclusion and its limits come first.
- Each version gets one bullet with a number and what changed.
- Honest "it is not a fixed rule" with a concrete counter-example.
- Open problems in a table, proposal as numbered steps with bold labels.
