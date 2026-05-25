interface ToastProps {
  message: string;
  type: "error" | "success";
  onClose: () => void;
}

export default function Toast({ message, type, onClose }: ToastProps) {
  return (
    <div
      className={`fixed top-4 left-1/2 -translate-x-1/2 z-[60] px-4 py-2 rounded-lg text-sm font-medium shadow-2xl ${
        type === "error"
          ? "bg-red-500/90 text-white"
          : "bg-[#00d4aa]/90 text-black"
      }`}
      style={{ animation: "slideDown 0.3s ease-out" }}
    >
      {message}
      <button onClick={onClose} className="ml-2 opacity-70 hover:opacity-100">
        ✕
      </button>
    </div>
  );
}
