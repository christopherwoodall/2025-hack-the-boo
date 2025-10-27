# Digital Alchemy

## History

```bash
bash -c "$(curl -fsSL https://gef.blah.cat/sh)"

gdb ./athanor

gef➤  starti
gef➤  b *0x555555555239  # Break at main
gef➤  c
gef➤  b *0x5555555553a9  # Break at first time check
gef➤  c
gef➤  set $rip = 0x5555555553b2 # Patch first time check
gef➤  b *0x55555555547a  # Break at second time check
gef➤  c
gef➤  set $rip = 0x555555555483 # Patch second time check
```

---
