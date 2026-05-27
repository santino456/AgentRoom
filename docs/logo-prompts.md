# AgentRoom Logo — AI 生成提示词

> 品牌色参考
> - 主背景：`#0f172a` (slate-900)
> - 强调色：`#00d4aa` (teal-400) / `#10b981` (emerald-500)
> - 辅助色：`#6366f1` (indigo-500)

---

## A. 房间里的机器人团队（具象）

**Midjourney:**
```
A minimalist logo of a cozy chat room with 3 cute robot characters inside, each robot has a different shape and color (teal, emerald, indigo), they are connected by speech bubbles, flat vector illustration style, clean geometric shapes, dark navy background #0f172a, neon teal accents #00d4aa, soft shadows, dribbble trending, 2D vector art, transparent background, centered composition, scalable icon design --ar 1:1 --v 6
```

**DALL-E 3:**
```
Create a minimalist flat vector logo for "AgentRoom". The design shows a simple room outline (like a hexagon or rounded square) containing 3 small cute robots of different colors (teal, emerald green, indigo). The robots are connected by speech bubbles. Clean geometric shapes, dark navy blue background (#0f172a), bright teal accents (#00d4aa). No text, no gradients, pure flat design. Transparent background. High resolution, centered.
```

**Stable Diffusion / Flux:**
```
masterpiece, best quality, minimalist logo, flat vector illustration, a cozy chat room with 3 cute robots inside, speech bubbles connecting them, geometric shapes, dark navy background, teal and emerald accents, clean lines, 2D vector art, transparent background, centered, scalable icon, dribbble style
Negative prompt: text, letters, words, gradient, 3D render, photorealistic, noisy, blurry, watermark
```

---

## B. 节点协作网络（抽象）

**Midjourney:**
```
An abstract minimalist logo of 4 glowing nodes connected by thin luminous lines forming a circular orbit pattern, the center is a subtle chat bubble shape, flat vector style, dark slate background #0f172a, nodes in teal #00d4aa and indigo #6366f1, clean geometric lines, futuristic tech aesthetic, simple and scalable, transparent background, centered --ar 1:1 --v 6
```

**DALL-E 3:**
```
Design an abstract minimalist logo: 4 glowing circular nodes connected by thin luminous lines, forming a circular orbit or constellation pattern. The center subtly suggests a chat bubble. Flat vector style, dark slate background (#0f172a), nodes in teal (#00d4aa) and indigo (#6366f1). No text, no gradients, clean geometric lines. Transparent background. Modern tech aesthetic.
```

**Stable Diffusion / Flux:**
```
masterpiece, best quality, abstract minimalist logo, 4 glowing nodes connected by luminous lines, circular orbit pattern, subtle chat bubble in center, flat vector, dark slate background, teal and indigo nodes, clean geometric lines, futuristic tech aesthetic, transparent background, centered, simple scalable design
Negative prompt: text, letters, gradient, 3D, photorealistic, cluttered, noisy
```

---

## C. 对话气泡机器人脸（亲切）

**Midjourney:**
```
A friendly minimalist mascot logo of a cute robot head shaped like a rounded speech bubble, two small circular eyes like code slashes //, a tiny antenna on top, flat vector illustration, dark navy background #0f172a, robot in teal #00d4aa with emerald #10b981 accents, kawaii-inspired but professional, clean lines, dribbble style, transparent background, centered --ar 1:1 --v 6
```

**DALL-E 3:**
```
Create a cute friendly mascot logo: a robot head shaped like a rounded speech bubble. It has two small circular eyes (like code comment slashes //) and a tiny antenna on top. Flat vector illustration style, dark navy background (#0f172a), robot colored in teal (#00d4aa) with emerald green (#10b981) accents. Kawaii-inspired but professional. No text, no gradients. Transparent background. Clean lines.
```

**Stable Diffusion / Flux:**
```
masterpiece, best quality, cute mascot logo, robot head shaped like a speech bubble, two circular eyes, tiny antenna, flat vector illustration, dark navy background, teal and emerald colors, kawaii but professional, clean lines, dribbble style, transparent background, centered, scalable icon
Negative prompt: text, letters, gradient, 3D render, realistic, scary, cluttered
```

---

## D. 极简字母标 AR（专业）

**Midjourney:**
```
A minimalist geometric lettermark logo of "AR", the letter A has a roof-like top suggesting a room, the letter R has a subtle robot antenna curve, flat vector style, dark slate background #0f172a, letters in teal #00d4aa with indigo #6366f1 shadow accent, clean typography, modern tech branding, scalable icon design, transparent background, centered --ar 1:1 --v 6
```

**DALL-E 3:**
```
Design a minimalist geometric lettermark logo using the letters "AR". The letter A has a roof-like triangular top suggesting a room. The letter R has a subtle curve suggesting a robot antenna. Flat vector style, dark slate background (#0f172a), letters in teal (#00d4aa) with indigo (#6366f1) accent. Modern tech branding, clean typography. No additional elements. Transparent background.
```

**Stable Diffusion / Flux:**
```
masterpiece, best quality, minimalist lettermark logo, letters "AR", geometric design, letter A with roof top, letter R with antenna curve, flat vector, dark slate background, teal and indigo colors, modern tech branding, clean typography, transparent background, centered, scalable
Negative prompt: text other than AR, gradient, 3D, photorealistic, cluttered, additional elements
```

---

## 通用负面提示词（所有方向通用）

```
text, letters, words, typography, watermark, signature, gradient, 3D render, photorealistic, noisy, blurry, cluttered background, complex details, realistic texture, shadows, reflections
```

## 生成后处理建议

1. **去背景**：用 remove.bg 或 Photoshop 抠成透明 PNG
2. **转矢量**：用 Vectorizer.AI 或 Illustrator 图像描摹，得到可无限缩放的 SVG
3. **做多版本**：
   - `logo-dark.png` — 亮色 logo，用于暗色背景
   - `logo-light.png` — 暗色 logo，用于亮色背景
   - `favicon.ico` — 16x16 / 32x32
   - `banner.png` — 1280x640（GitHub 社交预览）
