import { faceMetricsFromLandmarks, overlaySize } from "./fit.js";
import { paintFrameShape } from "./paint.js";

/**
 * Draw one frame at eye mid-point.
 * @param {CanvasRenderingContext2D} ctx
 * @param {object} frame
 * @param {number} midX
 * @param {number} midY
 * @param {number} angle rad
 * @param {number} pdPx pupil distance in px
 * @param {number} pdMm user PD mm
 * @param {number} [xOffset=0]
 */
export function drawFrameAt(ctx, frame, midX, midY, angle, pdPx, pdMm, xOffset = 0) {
  if (!frame) return;
  const { overlayW, overlayH } = overlaySize(frame, pdPx, pdMm);
  const cat = frame.category;
  ctx.save();
  const yOff =
    cat === "accessory" && (frame.style === "hat" || frame.style === "cap")
      ? -pdPx * 0.9
      : cat === "accessory" && frame.style === "necklace"
        ? pdPx * 1.35
        : pdPx * 0.02;
  ctx.translate(midX + xOffset, midY + yOff);
  ctx.rotate(angle);
  if (frame.style === "earring") {
    // Draw left earring
    ctx.save();
    ctx.translate(-pdPx * 1.15, pdPx * 0.5);
    paintFrameShape(ctx, frame, overlayW * 0.35, overlayH * 1.2);
    ctx.restore();
    // Draw right earring
    ctx.save();
    ctx.translate(pdPx * 1.15, pdPx * 0.5);
    paintFrameShape(ctx, frame, overlayW * 0.35, overlayH * 1.2);
    ctx.restore();
  } else if (frame.style === "hat" || frame.style === "cap") {
    const capBias = frame.style === "cap" ? -pdPx * 0.15 : 0;
    ctx.translate(0, capBias);
    paintFrameShape(ctx, frame, overlayW * 1.35, overlayH * 0.9);
  } else if (frame.style === "necklace") {
    paintFrameShape(ctx, frame, overlayW * 0.5, overlayH * 1.4);
  } else if (frame.style === "clip_on") {
    // Clip-on sun lenses: placed over the glasses area, smaller scale
    paintFrameShape(ctx, frame, overlayW * 0.8, overlayH * 0.8);
  } else {
    paintFrameShape(ctx, frame, overlayW, overlayH);
  }
  ctx.restore();
}

/**
 * Full glasses overlay for A or A|B compare mode.
 * @param {CanvasRenderingContext2D} ctx
 * @param {{left:[number,number], right:[number,number]}} face normalized landmarks
 * @param {object|null} selectedA
 * @param {object|null} selectedB
 * @param {boolean} compareMode
 * @param {number} pdMm
 */
export function drawGlassesOverlay(ctx, face, selectedA, selectedB, compareMode, pdMm) {
  const canvas = ctx.canvas;
  const w = canvas.width;
  const h = canvas.height;
  const m = faceMetricsFromLandmarks(face, w, h);

  if (compareMode && selectedA && selectedB) {
    // Split-view comparison with clear A/B panels
    // Left panel: Frame A
    ctx.save();
    ctx.beginPath();
    ctx.rect(0, 0, w / 2, h);
    ctx.clip();
    drawFrameAt(ctx, selectedA, m.midX, m.midY, m.angle, m.pdPx, pdMm, 0);
    ctx.restore();

    // Right panel: Frame B
    ctx.save();
    ctx.beginPath();
    ctx.rect(w / 2, 0, w / 2, h);
    ctx.clip();
    drawFrameAt(ctx, selectedB, m.midX, m.midY, m.angle, m.pdPx, pdMm, 0);
    ctx.restore();

    // Gold divider line
    ctx.strokeStyle = "#f5c518cc";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(w / 2, 0);
    ctx.lineTo(w / 2, h);
    ctx.stroke();

    // A/B labels with background badges
    const fontSize = Math.max(13, Math.round(w * 0.022));
    ctx.font = `bold ${fontSize}px system-ui`;
    ctx.textBaseline = "top";

    // Label A
    const textA = `A: ${selectedA.name || "Frame A"}`;
    const metricsA = ctx.measureText(textA);
    const padA = 6;
    ctx.fillStyle = "#1a1a2ecc";
    ctx.fillRect(8, 8, metricsA.width + padA * 2, fontSize + padA * 2);
    ctx.strokeStyle = "#f5c518";
    ctx.lineWidth = 1;
    ctx.strokeRect(8, 8, metricsA.width + padA * 2, fontSize + padA * 2);
    ctx.fillStyle = "#f5c518";
    ctx.fillText(textA, 8 + padA, 8 + padA);

    // Label B
    const textB = `B: ${selectedB.name || "Frame B"}`;
    const metricsB = ctx.measureText(textB);
    const padB = 6;
    const bx = w / 2 + 8;
    ctx.fillStyle = "#1a1a2ecc";
    ctx.fillRect(bx, 8, metricsB.width + padB * 2, fontSize + padB * 2);
    ctx.strokeStyle = "#f5c518";
    ctx.lineWidth = 1;
    ctx.strokeRect(bx, 8, metricsB.width + padB * 2, fontSize + padB * 2);
    ctx.fillStyle = "#f5c518";
    ctx.fillText(textB, bx + padB, 8 + padB);
  } else if (selectedA) {
    drawFrameAt(ctx, selectedA, m.midX, m.midY, m.angle, m.pdPx, pdMm, 0);
  }
}
