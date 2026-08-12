# google-slides (not published)

The live version of this skill builds decks against a specific employer's
branded PowerPoint template and is therefore not included here: it embeds a
Google Drive file ID for the template and the brand's hex palette.

The approach generalizes, and is worth rebuilding at a new employer:

1. **Cache the brand template.** Export the org's official `.pptx` template
   once and keep it in the work-automation repo (`assets/<org>-template.pptx`).
   Do not fetch it from Drive at runtime.
2. **Build on its layouts, don't restyle.** Add slides via the template's own
   layouts so theme colors, fonts, and the 16:9 canvas come through for free.
   `python-pptx` drives this.
3. **Centralize brand constants.** A small `<org>_deck.py` module exporting
   `load_blank_deck()`, `COLORS`, `FONT`, and `LAYOUT` keeps every deck
   consistent and confines brand values to one file.
4. **Upload with conversion.** Push the `.pptx` to Drive with
   `mimeType: application/vnd.google-apps.presentation` so it lands as a native
   Google Slides deck rather than an attached file.
5. **Clear unused placeholders.** Template layouts ship with prompt text; strip
   the placeholders you did not populate or they render as literal instructions.

Watch for: title placeholders are often short (~1 inch) with a large default
font, so long titles silently overflow into the body. Apply run-level font-size
overrides rather than resizing the placeholder.
