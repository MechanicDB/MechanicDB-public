# Assets

Marketing images referenced from the top-level `README.md` and used as the
Kaggle dataset cover.

- `kaggle-cover.png` — hero/cover banner (1600×640). The fix ranks, costs, and
  labor hours shown in the terminal card are the dataset's **real P0420 rows**,
  not mockup numbers.
- `kaggle-cover.html` — the banner's source. To regenerate after a design or
  data change:

  ```
  msedge --headless=new --disable-gpu --hide-scrollbars --window-size=1600,640
         --screenshot=kaggle-cover.png kaggle-cover.html
  ```
