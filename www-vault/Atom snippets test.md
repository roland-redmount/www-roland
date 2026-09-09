<!-- title: Atom snippets test -->
<!-- date: 2026-09-09 -->

A scratch post for checking that runnable snippets work. Delete it whenever.

Ask what two and three make. `s` is a variable, so it is filled in:

```atom
+ 2 + 3 = s
```

A variable can stand anywhere in the term, so the same table answers backwards:

```atom
+ 2 + x = 9
```

State a fact:

```atom
:assert foo 42 bar "baz"
```

Every snippet on the page shares one session, so this one finds a fact it never
stated itself:

```atom
foo 42 bar b
```

A plain code block is untouched, and stays a plain code block:

```
+ 2 + 3 = s
```
