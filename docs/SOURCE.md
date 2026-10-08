# Source and transparency

The original dashboard interfaces are copied with the owner's permission from [`Mason333xbt/writer`](https://github.com/Mason333xbt/writer), branch `claude/pensive-volta-lathuj`:

- `terminals/21-haiku-desk.html`
- `terminals/22-haiku-core.html`

They were designed as animated **simulations**. Market prices, model dialogue, execution events and historical PnL are generated in-browser and are not evidence of real trading performance. The *original versions* were initially copied without changes into `frontend/legacy/` and are accessible in earlier Git history. The current #21/#22 files in that folder are **static, no-JavaScript redesigns**: no simulator, countdown, speed/pause/reset buttons, AI API calls or generated trades. Both visibly retain `@alpha404ai` in a fixed watermark. Both rewritten HTML files are **standalone**: CSS and PNG logos are embedded, with no external dependencies. Separate editable CSS and logo PNG assets are also published in `frontend/legacy/mockup.css` and `frontend/assets/`.

All new code starts with paper trading; live orders require additional implementation, validation and explicit operator controls.
