type LogLevel = "log" | "info" | "warn" | "error";

interface LogEntry {
  level: LogLevel;
  message: string;
  timestamp: string;
}

const storageKey = "rshop_logs";

const save = (entry: LogEntry) => {
  try {
    const raw = localStorage.getItem(storageKey);
    const current: LogEntry[] = raw ? JSON.parse(raw) : [];
    current.push(entry);
    localStorage.setItem(storageKey, JSON.stringify(current).slice(-5000));
  } catch (error) {
    console.error("Logger storage error:", error);
  }
};

const serializeArgs = (args: unknown[]) =>
  args
    .map((value) => {
      if (typeof value === "string") return value;
      try {
        return JSON.stringify(value);
      } catch {
        return String(value);
      }
    })
    .join(" ");

const log = (level: LogLevel, ...args: unknown[]) => {
  const payload: LogEntry = {
    level,
    message: serializeArgs(args),
    timestamp: new Date().toISOString(),
  };
  save(payload);
  console[level](...args);
};

export const logger = {
  log: (...args: unknown[]) => log("log", ...args),
  info: (...args: unknown[]) => log("info", ...args),
  warn: (...args: unknown[]) => log("warn", ...args),
  error: (...args: unknown[]) => log("error", ...args),
  clearLogs: () => localStorage.removeItem(storageKey),
};
