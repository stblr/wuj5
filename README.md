# wuj5

Convert Wii UI formats to JSON5 and vice versa.

## Supported formats

| Format | Read | Write | Check |
| :----- | :--- | :---- | :---- |
| BRCTR  | Yes  | Yes   |       |
| BRLYT  | WIP  |       |       |

## How to use

```bash
wuj5.py decode Control.brctr # Control.brctr -> Control.json5
cp Control.json5 MyControl.json5
# Do some changes to MyControl.json5 with a text editor
wuj5.py encode MyControl.json5 # MyControl.json5 -> MyControl.brctr
```
