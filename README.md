# wuj5

Convert Wii UI formats to JSON5 and vice versa.

## Supported formats

| Format | Read | Write | Check |
| :----- | :--- | :---- | :---- |
| BRCTR  | Yes  | Yes   |       |
| BRLAN  | Yes  | Yes   |       |
| BRLYT  | WIP  | WIP   |       |

## How to use

```bash
wuj5.py decode Control.brctr # Control.brctr -> Control.brctr.json5
cp Control.brctr.json5 MyControl.brctr.json5
# Do some changes to MyControl.brctr.json5 with a text editor
wuj5.py encode MyControl.brctr.json5 # MyControl.brctr.json5 -> MyControl.brctr
```
