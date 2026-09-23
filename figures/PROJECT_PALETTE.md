# Project colour palette

Canonical order supplied by the researcher:

```r
colorlist <- c("#f4cee1", "#c5d9df", "#e16db7", "#908ebc", "#af88bb", "#dedbee", "#f07590", "#dfb9d5", "#b099b5", "#5394c3", "#b8a89f")
```

Rules:

- Categorical charts use colours in the supplied order unless a fixed semantic mapping is declared.
- Continuous scales use ordered anchors selected only from this palette.
- White is reserved for no-data/zero map cells and plot background.
- Text and boundary greys are functional neutrals, not data colours.
- Every figure manifest records the palette used so later figures remain reproducible.
