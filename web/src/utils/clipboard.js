import { showFailToast, showSuccessToast } from "vant";

/**
 * 复制文本，兼容 HTTP 环境。
 * navigator.clipboard 仅 secure context（HTTPS/localhost）可用，
 * 线上 HTTP 用 execCommand 降级。
 */
export function copyText(text, successMsg = "已复制") {
  if (navigator.clipboard?.writeText) {
    navigator.clipboard.writeText(text).then(
      () => showSuccessToast(successMsg),
      () => fallbackCopy(text, successMsg),
    );
    return;
  }
  fallbackCopy(text, successMsg);
}

function fallbackCopy(text, successMsg) {
  const ta = document.createElement("textarea");
  ta.value = text;
  ta.style.position = "fixed";
  ta.style.opacity = "0";
  document.body.appendChild(ta);
  ta.select();
  const ok = document.execCommand("copy");
  document.body.removeChild(ta);
  if (ok) {
    showSuccessToast(successMsg);
  } else {
    showFailToast("复制失败，请长按手动复制");
  }
}
