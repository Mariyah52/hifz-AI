# fonts/

Amiri and Scheherazade New currently load from Google Fonts (see the
`<link>` in `index.html`) — that works out of the box, no files needed here.

If you'd rather self-host (offline support, no Google Fonts request):

1. Get the OFL `.ttf`/`.otf` releases:
   - Amiri: https://github.com/aliftype/amiri
   - Scheherazade New: https://software.sil.org/scheherazade/
2. Convert to `.woff2` and place them in this folder as
   `Amiri-Regular.woff2`, `Amiri-Bold.woff2`, `ScheherazadeNew-Regular.woff2`.
3. Uncomment the matching `@font-face` rules in `src/styles/tokens.css`.
4. Remove the Amiri/Scheherazade New families from the Google Fonts
   `<link>` in `index.html`.

Steps 3 and 4 have to happen together — leaving both the local files and
the Google Fonts link active at once means the (until-then-missing) local
font 404s and silently wins the cascade over the working Google version.
