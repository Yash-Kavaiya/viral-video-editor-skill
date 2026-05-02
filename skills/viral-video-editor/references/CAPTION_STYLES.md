# Caption Animation Style Catalog

Use these style presets in `caption_engine.py` based on user preference or platform.

## Style 1: BOLD_POP (Default)
```css
.word {
  font-family: "Arial Black", sans-serif;
  font-weight: 900;
  font-size: 22px;
  color: white;
  text-transform: uppercase;
  text-shadow: -2px -2px 0 #000, 2px -2px 0 #000, -2px 2px 0 #000, 2px 2px 0 #000;
  padding: 4px 6px;
}
.word-being-narrated {
  color: #FFD700;  /* Gold highlight */
  transform: scale(1.1);
}
```

## Style 2: KARAOKE
```css
.word { color: #AAAAAA; font-size: 20px; }
.word-being-narrated { color: #FF4444; font-size: 22px; }
```

## Style 3: MINIMAL_WHITE
```css
.word {
  color: white;
  font-size: 18px;
  background: rgba(0,0,0,0.5);
  border-radius: 4px;
  padding: 2px 5px;
}
.word-being-narrated { background: rgba(0,0,0,0.8); }
```

## Style 4: SPEAKER_COLOR
- Speaker 1: #4FC3F7 (blue)
- Speaker 2: #81C784 (green)
- Speaker 3: #FFB74D (orange)
- Unknown: white

## Animation Types

| Animation | Trigger | Best For |
|-----------|---------|----------|
| `SlideIn(direction="up")` | First segment | Intros |
| `ZoomIn()` | Each new segment | Energy |
| `FadeIn()` | Calm content | Minimal style |
| `SlideIn(direction="down")` | Emphasis moments | Drama |

## Positioning

- **Bottom-third**: `y=75%` — Standard, doesn't cover face
- **Center**: `y=50%` — High-impact moments
- **Top-third**: `y=15%` — When lower-third has graphics
