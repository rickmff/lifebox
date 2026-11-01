# Flow video

Source of `docs/assets/lifebox-flow.mp4` and `lifebox-flow.gif`: an SVG animation in
`flow.html`, rendered frame by frame with Playwright and encoded with ffmpeg.

```bash
# Geist fonts (SIL Open Font License), not committed
npm pack geist && tar xzf geist-*.tgz
mkdir -p docs/video/fonts
cp package/dist/fonts/geist-sans/Geist-Variable.woff2 \
   package/dist/fonts/geist-mono/GeistMono-Variable.woff2 docs/video/fonts/

node docs/video/render.js .work/frames

ffmpeg -y -framerate 30 -i .work/frames/f%04d.png -c:v libx264 -preset slow -crf 18 \
  -pix_fmt yuv420p -movflags +faststart docs/assets/lifebox-flow.mp4

ffmpeg -y -i docs/assets/lifebox-flow.mp4 -vf "fps=15,scale=960:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=64:stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle" \
  -loop 0 docs/assets/lifebox-flow.gif
```

Without the fonts the page falls back to the system sans-serif.
