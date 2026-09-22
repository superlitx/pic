# Matters App Logo — 六款材质交付

`outputs/00-six-variant-contact-sheet.png` 是整套预览，六张独立成品为：

- `outputs/01-orange-inset-flock-final-1024.png`：橙色短绒填充凹面，1024 × 1024，sRGB；保留白色背景与接地投影。
- `outputs/02-iridescent-gradient-final-1024.png`：彩虹软胶，1024 × 1024，sRGB。
- `outputs/03-toast-final-1024.png`：面包，1024 × 1024，sRGB。
- `outputs/04-biscuit-final-1024.png`：饼干，1024 × 1024，sRGB。
- `outputs/04-biscuit-final-4096.png`：饼干高分辨率版，4096 × 4096，sRGB。
- `outputs/05-gold-glass-final-1024.png`：金色玻璃，1024 × 1024，sRGB。
- `outputs/06-holographic-final-1024.png`：镭射，1024 × 1024，sRGB。

## 不可修改的规则

- `assets/matters.svg` 是正面几何的唯一来源。
- Blender 模型只约束正面顶面、位置、尺寸、深度和区域关系。
- 已确认参考图的材质、五官、背景和投影不得重新生成或局部重画。
- 只允许对整张参考图做一次统一配准。
- 侧面厚度、倒角、颗粒、接触阴影可以超出正面顶面的 SVG 范围。
- Figma 交付必须经过正确的 ICC 转换并嵌入 sRGB，禁止丢失或仅重贴色彩标签。
- 必须先通过单张样板验证，再处理下一张。

完整执行规则保存在仓库根目录的
`skills/locked-svg-material-render/SKILL.md`。

## 文件结构

- `assets/`：原始 SVG、权威遮罩、六款材质参考图和 sRGB 色彩配置。
- `models/`：Blender 正面约束模型。
- `outputs/`：可直接导入 Figma 的最终图片。
- `proofs/`：模型叠加图、正面 Alpha 验证和配准报告。
- `scripts/`：可移机运行的模型与配准脚本。
- `SHA256SUMS`：交付文件校验值。

## 在另一台电脑复现

安装 Python 3.12，并在虚拟环境中安装：

```bash
python3 -m pip install -r AppLogo_Blender/approved-delivery/requirements.txt
```

重新生成六张 1024 成品：

```bash
python3 AppLogo_Blender/approved-delivery/scripts/register_reference.py \
  --source AppLogo_Blender/approved-delivery/assets/01-orange-inset-flock-reference-1254.png \
  --slug 01-orange-inset-flock \
  --support-kernel 151 \
  --erode-kernel 91

python3 AppLogo_Blender/approved-delivery/scripts/register_reference.py \
  --source AppLogo_Blender/approved-delivery/assets/02-iridescent-gradient-reference-1024.png \
  --slug 02-iridescent-gradient

python3 AppLogo_Blender/approved-delivery/scripts/register_reference.py \
  --source AppLogo_Blender/approved-delivery/assets/toast-reference-1254.png \
  --slug 03-toast \
  --support-kernel 151 \
  --erode-kernel 91

python3 AppLogo_Blender/approved-delivery/scripts/register_reference.py \
  --source AppLogo_Blender/approved-delivery/assets/biscuit-reference-4096.png \
  --slug 04-biscuit \
  --support-kernel 111 \
  --erode-kernel 61 \
  --highres 4096

python3 AppLogo_Blender/approved-delivery/scripts/register_reference.py \
  --source AppLogo_Blender/approved-delivery/assets/05-gold-glass-reference-1024.png \
  --slug 05-gold-glass

python3 AppLogo_Blender/approved-delivery/scripts/register_reference.py \
  --source AppLogo_Blender/approved-delivery/assets/06-holographic-reference-1024.png \
  --slug 06-holographic
```

单独重新生成饼干高分辨率版：

```bash
python3 AppLogo_Blender/approved-delivery/scripts/register_reference.py \
  --source AppLogo_Blender/approved-delivery/assets/biscuit-reference-4096.png \
  --slug 04-biscuit \
  --support-kernel 111 \
  --erode-kernel 61 \
  --highres 4096
```

重新生成 Blender 约束模型：

```bash
blender --background --factory-startup \
  --python AppLogo_Blender/approved-delivery/scripts/build_constraint_model.py
```

安装本项目 skill：

```bash
mkdir -p ~/.codex/skills
cp -R skills/locked-svg-material-render ~/.codex/skills/
```
