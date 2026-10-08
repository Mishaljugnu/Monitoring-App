const { app, BrowserWindow, shell } = require("electron");
const path = require("path");
const { spawn } = require("child_process");

const isDev = !app.isPackaged;
let backendProcess = null;

function pythonCommand() {
  return process.platform === "win32" ? "python" : "python3";
}

function startBackend() {
  if (!isDev || process.env.NETVISION_SKIP_BACKEND === "1") return;

  const backendDir = path.resolve(__dirname, "..", "..", "backend");
  backendProcess = spawn(
    process.env.NETVISION_PYTHON || pythonCommand(),
    ["-m", "uvicorn", "app.main:app", "--app-dir", backendDir, "--host", "127.0.0.1", "--port", "8000"],
    { stdio: "inherit", windowsHide: true }
  );

  backendProcess.on("error", (error) => {
    console.error("Could not start NetVision backend:", error.message);
  });
}

function stopBackend() {
  if (backendProcess && !backendProcess.killed) backendProcess.kill();
  backendProcess = null;
}

function createWindow() {
  const window = new BrowserWindow({
    width: 1560,
    height: 980,
    minWidth: 1200,
    minHeight: 760,
    backgroundColor: "#020617",
    autoHideMenuBar: true,
    webPreferences: {
      contextIsolation: true,
      sandbox: true
    }
  });

  if (isDev) {
    window.loadURL("http://127.0.0.1:5173");
  } else {
    window.loadFile(path.join(__dirname, "..", "dist", "index.html"));
  }

  window.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: "deny" };
  });
}

app.whenReady().then(() => {
  startBackend();
  createWindow();
  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("before-quit", stopBackend);
app.on("window-all-closed", () => {
  stopBackend();
  if (process.platform !== "darwin") app.quit();
});
