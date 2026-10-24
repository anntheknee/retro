Follow-through: judge the `previous_findings` in your input (skip this if it has none). Each gets a verdict: worked, didn't work, not adopted, or no longer relevant. Judge from what changed (settings, installs, usage in the Window, whether the problem came back). A not-adopted Finding comes back as a new Finding only if the problem got worse. An Overlap that still exists comes back every Retro, labelled "raised before". After a merge or removal that was applied, check the replacement got used. Return the verdict rows first, as table rows:
`| <short summary of the fix> | <verdict> | <origin: Retro, /insights or web> |`

Then return only Findings in this layout, with your categories, no numbers, origin `via Retro`:

```
### <category> · <project or "all"> · via Retro
**Problem**: <one or two lines, with the numbers>
**Solutions**:
- **a.** <the exact change: file and edit, or command>. Fit: <…>. Adoption: <…>.
```

Up to three self-contained solutions each. No evidence lines, no status. Skip a category with nothing worth saying.
