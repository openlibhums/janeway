# Sequence fields

We use several patterns across Janeway to let users set the sequence of things, most commonly with a `PositiveIntegerField`.

Because we sometimes expose this number to end users in form inputs, it is worth thinking about the usability of the default value. The number 1 is low enough to be easy for end users to manipulate. Zero is sometimes most convenient from a programming perspective, but avoid it if possible, since it can be counter-intuitive for non-programmers.

```py
sequence = models.PositiveIntegerField(default=1)
```

Of course, it is best if end users do not have to deal with this number at all. User interfaces should use accessible buttons that move things up or down in the sequence. This allows us to write an algorithm to check that multiple things have not been given the same sequence, and it keeps the user from having to recall off-screen information about the order of other items whilst performing an action.
