using System;
using System.Buffers;
using System.Collections.Generic;
using System.IO;
using System.Runtime.InteropServices;
using System.Text;
using System.Text.Json;

// .NET bridge for plcommpro.dll.
// Reads one JSON request from --request (or --request-file) and prints one JSON response.

static class PlcommproNative
{
    private static IntPtr _loaded = IntPtr.Zero;

    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    private static extern bool SetDllDirectory(string? lpPathName);

    static PlcommproNative()
    {
        NativeLibrary.SetDllImportResolver(typeof(PlcommproNative).Assembly, (name, assembly, path) =>
        {
            if (string.Equals(name, "plcommpro.dll", StringComparison.OrdinalIgnoreCase) && _loaded != IntPtr.Zero)
            {
                return _loaded;
            }
            return IntPtr.Zero;
        });
    }

    public static void EnsureLoaded(string? dllPath)
    {
        if (_loaded != IntPtr.Zero)
            return;

        if (!string.IsNullOrWhiteSpace(dllPath))
        {
            try
            {
                var dir = Path.GetDirectoryName(dllPath);
                if (!string.IsNullOrWhiteSpace(dir) && Directory.Exists(dir))
                {
                    // Help Windows resolve plcommpro.dll dependencies (crypto, comms, etc.).
                    SetDllDirectory(dir);
                    var path = Environment.GetEnvironmentVariable("PATH") ?? "";
                    if (!path.Contains(dir, StringComparison.OrdinalIgnoreCase))
                    {
                        Environment.SetEnvironmentVariable("PATH", dir + ";" + path);
                    }
                }
            }
            catch { }
            _loaded = NativeLibrary.Load(dllPath);
            return;
        }

        // Default resolution (PATH / system search). On many installs it lives in SysWOW64.
        _loaded = NativeLibrary.Load("plcommpro.dll");
    }

    [DllImport("plcommpro.dll", EntryPoint = "PullLastError", CallingConvention = CallingConvention.StdCall)]
    public static extern int PullLastError();

    [DllImport("plcommpro.dll", EntryPoint = "Connect", CallingConvention = CallingConvention.StdCall)]
    public static extern int Connect(IntPtr connStr);

    [DllImport("plcommpro.dll", EntryPoint = "Disconnect", CallingConvention = CallingConvention.StdCall)]
    public static extern void Disconnect(int handle);

    [DllImport("plcommpro.dll", EntryPoint = "GetDeviceParam", CallingConvention = CallingConvention.StdCall)]
    public static extern int GetDeviceParam(int handle, IntPtr outBuf, int outLen, IntPtr items);

    [DllImport("plcommpro.dll", EntryPoint = "SetDeviceParam", CallingConvention = CallingConvention.StdCall)]
    public static extern int SetDeviceParam(int handle, IntPtr items);

    [DllImport("plcommpro.dll", EntryPoint = "GetDeviceDataCount", CallingConvention = CallingConvention.StdCall)]
    public static extern int GetDeviceDataCount(int handle, IntPtr table, IntPtr filter, IntPtr options);

    [DllImport("plcommpro.dll", EntryPoint = "GetDeviceData", CallingConvention = CallingConvention.StdCall)]
    public static extern int GetDeviceData(int handle, IntPtr outBuf, int outLen, IntPtr table, IntPtr fields, IntPtr filter, IntPtr options);

    [DllImport("plcommpro.dll", EntryPoint = "DeleteDeviceData", CallingConvention = CallingConvention.StdCall)]
    public static extern int DeleteDeviceData(int handle, IntPtr table, IntPtr filter, IntPtr options);

    [DllImport("plcommpro.dll", EntryPoint = "SetDeviceData", CallingConvention = CallingConvention.StdCall)]
    public static extern int SetDeviceData(int handle, IntPtr table, IntPtr data, IntPtr options);

    [DllImport("plcommpro.dll", EntryPoint = "EnableDevice", CallingConvention = CallingConvention.StdCall)]
    public static extern int EnableDevice(int handle, int enable);

    [DllImport("plcommpro.dll", EntryPoint = "SearchDevice", CallingConvention = CallingConvention.StdCall)]
    public static extern int SearchDevice(IntPtr protocol, IntPtr address, IntPtr outBuf);

    [DllImport("plcommpro.dll", EntryPoint = "ModifyIPAddress", CallingConvention = CallingConvention.StdCall)]
    public static extern int ModifyIPAddress(IntPtr protocol, IntPtr address, IntPtr payload);

    [DllImport("plcommpro.dll", EntryPoint = "ControlDevice", CallingConvention = CallingConvention.StdCall)]
    public static extern int ControlDevice(int handle, int operation, int doorId, int index, int state, int time, IntPtr reserved);
}

static class Util
{
    public static byte[] ToLatin1Z(string s)
    {
        var bytes = Encoding.Latin1.GetBytes(s);
        var z = new byte[bytes.Length + 1];
        Buffer.BlockCopy(bytes, 0, z, 0, bytes.Length);
        z[z.Length - 1] = 0;
        return z;
    }

    public static string FromLatin1Z(byte[] bytes)
    {
        var idx = Array.IndexOf(bytes, (byte)0);
        if (idx < 0) idx = bytes.Length;
        return Encoding.Latin1.GetString(bytes, 0, idx);
    }

    public static IntPtr AllocZ(string s, out GCHandle handle)
    {
        var b = ToLatin1Z(s);
        handle = GCHandle.Alloc(b, GCHandleType.Pinned);
        return handle.AddrOfPinnedObject();
    }

    public static IntPtr AllocBytes(byte[] b, out GCHandle handle)
    {
        handle = GCHandle.Alloc(b, GCHandleType.Pinned);
        return handle.AddrOfPinnedObject();
    }
}

record BridgeResponse(bool ok, int result, string data, int last_error);

class Program
{
    static int Main(string[] args)
    {
        try
        {
            string requestJson = "";
            string requestFile = "";
            for (int i = 0; i < args.Length; i++)
            {
                if (args[i] == "--request-file" && i + 1 < args.Length)
                {
                    requestFile = args[i + 1] ?? "";
                    continue;
                }
                if (args[i] == "--request" && i + 1 < args.Length)
                {
                    requestJson = args[i + 1] ?? "";
                    continue;
                }
            }

            if (!string.IsNullOrWhiteSpace(requestFile))
            {
                requestJson = File.ReadAllText(requestFile);
            }

            if (string.IsNullOrWhiteSpace(requestJson))
            {
                Write(new BridgeResponse(false, -1, "missing --request or --request-file", 0));
                return 2;
            }

            using var doc = JsonDocument.Parse(requestJson);
            var root = doc.RootElement;

            string action = root.TryGetProperty("action", out var a) ? (a.GetString() ?? "") : "";
            action = action.Trim().ToLowerInvariant();

            string? dllPath = root.TryGetProperty("dll_path", out var dp) ? dp.GetString() : null;

            PlcommproNative.EnsureLoaded(dllPath);

            // Fast sanity check: only load the DLL and exit.
            if (action == "load_only")
            {
                Write(new BridgeResponse(true, 1, "loaded", 0));
                return 0;
            }

            if (action == "search_device")
            {
                string? address = root.TryGetProperty("address", out var ad) ? ad.GetString() : null;
                return HandleSearchDevice(address);
            }

            if (action == "modify_ip")
            {
                string payload = root.TryGetProperty("payload", out var p) ? (p.GetString() ?? "") : "";
                string? address = root.TryGetProperty("address", out var ad) ? ad.GetString() : null;
                return HandleModifyIp(payload, address);
            }

            // Remaining actions require connected handle.
            var comm = root.TryGetProperty("comminfo", out var ci) ? ci : default;
            int handle = Connect(comm);
            if (handle <= 0)
            {
                int lastErr = SafeLastError();
                Write(new BridgeResponse(false, handle, "connect failed", lastErr));
                return 0;
            }

            try
            {
                return action switch
                {
                    "connect_only" => HandleConnectOnly(handle),
                    "get_options" => HandleGetOptions(handle, root),
                    "set_options" => HandleSetOptions(handle, root),
                    "data_count" => HandleDataCount(handle, root),
                    "query_data" => HandleQueryData(handle, root),
                    "delete_data" => HandleDeleteData(handle, root),
                    "set_data" => HandleSetData(handle, root),
                    "enable_device" => HandleEnableDevice(handle, root),
                    "control_device" => HandleControlDevice(handle, root, operation: 1),
                    "cancel_alarm" => HandleControlDevice(handle, root, operation: 2),
                    "reboot" => HandleControlDevice(handle, root, operation: 3),
                    "control_normal_open" => HandleControlDevice(handle, root, operation: 4),
                    _ => UnknownAction(handle)
                };
            }
            finally
            {
                try { PlcommproNative.Disconnect(handle); } catch { }
            }
        }
        catch (Exception ex)
        {
            Write(new BridgeResponse(false, -500, $"exception: {ex.Message}", SafeLastError()));
            return 0;
        }
    }

    static int SafeLastError()
    {
        try { return PlcommproNative.PullLastError(); } catch { return 0; }
    }

    static void Write(BridgeResponse resp)
    {
        var json = JsonSerializer.Serialize(resp);
        Console.Out.Write(json);
    }

    static int HandleSearchDevice(string? address)
    {
        GCHandle hProto = default, hAddr = default;
        IntPtr pProto = Util.AllocZ("UDP", out hProto);
        string addr = string.IsNullOrWhiteSpace(address) ? "255.255.255.255" : address.Trim();
        IntPtr pAddr = Util.AllocZ(addr, out hAddr);

        // Large output buffer.
        byte[] outBuf = new byte[65536];
        GCHandle hOut = GCHandle.Alloc(outBuf, GCHandleType.Pinned);
        try
        {
            int ret = PlcommproNative.SearchDevice(pProto, pAddr, hOut.AddrOfPinnedObject());
            int lastErr = SafeLastError();
            string data = ret >= 0 ? Util.FromLatin1Z(outBuf) : "";
            Write(new BridgeResponse(ret >= 0, ret, data, lastErr));
            return 0;
        }
        finally
        {
            if (hOut.IsAllocated) hOut.Free();
            if (hProto.IsAllocated) hProto.Free();
            if (hAddr.IsAllocated) hAddr.Free();
        }
    }

    static int HandleModifyIp(string payload, string? address)
    {
        GCHandle hProto = default, hAddr = default, hPayload = default;
        IntPtr pProto = Util.AllocZ("UDP", out hProto);
        string addr = string.IsNullOrWhiteSpace(address) ? "255.255.255.255" : address.Trim();
        IntPtr pAddr = Util.AllocZ(addr, out hAddr);
        IntPtr pPayload = Util.AllocZ(payload, out hPayload);
        try
        {
            int ret = PlcommproNative.ModifyIPAddress(pProto, pAddr, pPayload);
            int lastErr = SafeLastError();
            Write(new BridgeResponse(ret >= 0, ret, "", lastErr));
            return 0;
        }
        finally
        {
            if (hProto.IsAllocated) hProto.Free();
            if (hAddr.IsAllocated) hAddr.Free();
            if (hPayload.IsAllocated) hPayload.Free();
        }
    }

    static int HandleConnectOnly(int handle)
    {
        // If we reached here, Connect() succeeded.
        Write(new BridgeResponse(true, handle, "connected", SafeLastError()));
        return 0;
    }

    static int Connect(JsonElement comm)
    {
        int commType = GetInt(comm, "comm_type", 1);
        string protocol = GetString(comm, "protocol", "").Trim();
        string ip = GetString(comm, "ipaddress", "");
        int port = GetInt(comm, "ip_port", 4370);
        string passwd = GetString(comm, "password", "");
        int timeout = GetInt(comm, "timeout", 3000);

        string connStr;
        if (commType == 1)
        {
            var proto = string.IsNullOrWhiteSpace(protocol) ? "TCP" : protocol;
            connStr = $"protocol={proto},ipaddress={ip},port={port},timeout={timeout}";
            if (!string.IsNullOrWhiteSpace(passwd))
            {
                connStr += $",passwd={passwd}";
                // Newer panels / SDKs may use 'commKey' for encrypted communication.
                // Keep passwd for backward compatibility; sending both is safe.
                connStr += $",commKey={passwd}";
            }
        }
        else
        {
            string comPort = GetString(comm, "com_port", "COM1");
            string baud = GetString(comm, "baudrate", "9600");
            int devId = GetInt(comm, "com_address", 1);
            connStr = $"protocol=RS485,port={comPort},baudrate={baud}bps,deviceid={devId},timeout={timeout}";
            if (!string.IsNullOrWhiteSpace(passwd))
            {
                connStr += $",passwd={passwd}";
            }
        }

        GCHandle h;
        IntPtr p = Util.AllocZ(connStr, out h);
        try
        {
            int ret = PlcommproNative.Connect(p);
            if (ret > 0) return ret;

            int err = SafeLastError();
            if (err > 0) err = -err;
            return err != 0 ? err : -1;
        }
        finally
        {
            if (h.IsAllocated) h.Free();
        }
    }

    static int HandleGetOptions(int handle, JsonElement root)
    {
        string items = root.TryGetProperty("items", out var it) ? (it.GetString() ?? "") : "";

        byte[] outBuf = new byte[2048];
        GCHandle hOut = GCHandle.Alloc(outBuf, GCHandleType.Pinned);

        GCHandle hItems = default;
        IntPtr pItems = Util.AllocZ(items, out hItems);

        try
        {
            int ret = PlcommproNative.GetDeviceParam(handle, hOut.AddrOfPinnedObject(), outBuf.Length, pItems);
            int lastErr = SafeLastError();
            string data = ret >= 0 ? Util.FromLatin1Z(outBuf) : "";
            Write(new BridgeResponse(ret >= 0, ret, data, lastErr));
            return 0;
        }
        finally
        {
            if (hOut.IsAllocated) hOut.Free();
            if (hItems.IsAllocated) hItems.Free();
        }
    }

    static int HandleSetOptions(int handle, JsonElement root)
    {
        string items = root.TryGetProperty("items", out var it) ? (it.GetString() ?? "") : "";
        GCHandle hItems = default;
        IntPtr pItems = Util.AllocZ(items, out hItems);
        try
        {
            int ret = PlcommproNative.SetDeviceParam(handle, pItems);
            int lastErr = SafeLastError();
            Write(new BridgeResponse(ret >= 0, ret, "", lastErr));
            return 0;
        }
        finally
        {
            if (hItems.IsAllocated) hItems.Free();
        }
    }

    static int HandleDataCount(int handle, JsonElement root)
    {
        string table = root.TryGetProperty("table", out var t) ? (t.GetString() ?? "") : "";
        GCHandle hTable = default, hEmpty = default;
        IntPtr pTable = Util.AllocZ(table, out hTable);
        IntPtr pEmpty = Util.AllocZ("", out hEmpty);
        try
        {
            int ret = PlcommproNative.GetDeviceDataCount(handle, pTable, pEmpty, pEmpty);
            int lastErr = SafeLastError();
            Write(new BridgeResponse(ret >= 0, ret, "", lastErr));
            return 0;
        }
        finally
        {
            if (hTable.IsAllocated) hTable.Free();
            if (hEmpty.IsAllocated) hEmpty.Free();
        }
    }

    static int HandleQueryData(int handle, JsonElement root)
    {
        string table = root.TryGetProperty("table", out var t) ? (t.GetString() ?? "") : "";
        string fields = root.TryGetProperty("fields", out var f) ? (f.GetString() ?? "*") : "*";
        string filter = root.TryGetProperty("filter", out var fl) ? (fl.GetString() ?? "") : "";
        string option = root.TryGetProperty("option", out var op) ? (op.GetString() ?? "") : "";
        int bufLen = root.TryGetProperty("buffer_len", out var bl) ? (bl.GetInt32()) : 2097152;
        if (bufLen < 1024) bufLen = 1024;

        byte[] outBuf = ArrayPool<byte>.Shared.Rent(bufLen);
        Array.Clear(outBuf, 0, bufLen);
        GCHandle hOut = GCHandle.Alloc(outBuf, GCHandleType.Pinned);

        GCHandle hTable = default, hFields = default, hFilter = default, hOpt = default;
        IntPtr pTable = Util.AllocZ(table, out hTable);
        IntPtr pFields = Util.AllocZ(fields, out hFields);
        IntPtr pFilter = Util.AllocZ(filter, out hFilter);
        IntPtr pOpt = Util.AllocZ(option, out hOpt);

        try
        {
            int ret = PlcommproNative.GetDeviceData(handle, hOut.AddrOfPinnedObject(), bufLen, pTable, pFields, pFilter, pOpt);
            int lastErr = SafeLastError();
            string data = ret >= 0 ? Util.FromLatin1Z(outBuf) : "";
            Write(new BridgeResponse(ret >= 0, ret, data, lastErr));
            return 0;
        }
        finally
        {
            if (hOut.IsAllocated) hOut.Free();
            if (hTable.IsAllocated) hTable.Free();
            if (hFields.IsAllocated) hFields.Free();
            if (hFilter.IsAllocated) hFilter.Free();
            if (hOpt.IsAllocated) hOpt.Free();
            ArrayPool<byte>.Shared.Return(outBuf);
        }
    }

    static int HandleDeleteData(int handle, JsonElement root)
    {
        string table = root.TryGetProperty("table", out var t) ? (t.GetString() ?? "") : "";
        string filter = root.TryGetProperty("filter", out var fl) ? (fl.GetString() ?? "") : "";

        GCHandle hTable = default, hFilter = default, hOpt = default;
        IntPtr pTable = Util.AllocZ(table, out hTable);
        IntPtr pFilter = Util.AllocZ(filter, out hFilter);
        IntPtr pOpt = Util.AllocZ("", out hOpt);

        try
        {
            int ret = PlcommproNative.DeleteDeviceData(handle, pTable, pFilter, pOpt);
            int lastErr = SafeLastError();
            Write(new BridgeResponse(ret >= 0, ret, "", lastErr));
            return 0;
        }
        finally
        {
            if (hTable.IsAllocated) hTable.Free();
            if (hFilter.IsAllocated) hFilter.Free();
            if (hOpt.IsAllocated) hOpt.Free();
        }
    }

    static int HandleSetData(int handle, JsonElement root)
    {
        string table = root.TryGetProperty("table", out var t) ? (t.GetString() ?? "") : "";
        string data = root.TryGetProperty("data", out var d) ? (d.GetString() ?? "") : "";
        string option = root.TryGetProperty("option", out var op) ? (op.GetString() ?? "") : "";

        GCHandle hTable = default, hData = default, hOpt = default;
        IntPtr pTable = Util.AllocZ(table, out hTable);
        IntPtr pData = Util.AllocZ(data, out hData);
        IntPtr pOpt = Util.AllocZ(option, out hOpt);

        try
        {
            int ret = PlcommproNative.SetDeviceData(handle, pTable, pData, pOpt);
            int lastErr = SafeLastError();
            Write(new BridgeResponse(ret >= 0, ret, "", lastErr));
            return 0;
        }
        finally
        {
            if (hTable.IsAllocated) hTable.Free();
            if (hData.IsAllocated) hData.Free();
            if (hOpt.IsAllocated) hOpt.Free();
        }
    }

    static int HandleEnableDevice(int handle, JsonElement root)
    {
        int enable = GetInt(root, "enable", 1);
        try
        {
            int ret = PlcommproNative.EnableDevice(handle, enable);
            int lastErr = SafeLastError();
            Write(new BridgeResponse(ret >= 0, ret, "", lastErr));
            return 0;
        }
        catch
        {
            Write(new BridgeResponse(false, -1, "EnableDevice not available", SafeLastError()));
            return 0;
        }
    }

    static int HandleControlDevice(int handle, JsonElement root, int operation)
    {
        int door = GetInt(root, "door", 0);
        int index = GetInt(root, "index", 0);
        int state = GetInt(root, "state", 0);
        int time = GetInt(root, "time", 0);
        string reserved = root.TryGetProperty("reserved", out var rv) ? (rv.GetString() ?? "") : "";

        // Match legacy semantics from ZKAccess devcomm.py:
        // op=1: door open/close uses (door, index, state)
        // op=2: cancel alarm uses (door, 0, 0)
        // op=3: reboot uses (0, 0, 0)
        // op=4: normal open uses (door, state, 0)
        if (operation == 2)
        {
            index = 0;
            state = 0;
        }
        else if (operation == 3)
        {
            door = 0;
            index = 0;
            state = 0;
        }
        else if (operation == 4)
        {
            index = state;
            state = 0;
        }

        GCHandle hRes = default;
        IntPtr pRes = Util.AllocZ(reserved, out hRes);
        try
        {
            int ret = PlcommproNative.ControlDevice(handle, operation, door, index, state, time, pRes);
            int lastErr = SafeLastError();
            Write(new BridgeResponse(ret >= 0, ret, "", lastErr));
            return 0;
        }
        finally
        {
            if (hRes.IsAllocated) hRes.Free();
        }
    }

    static int UnknownAction(int handle)
    {
        Write(new BridgeResponse(false, -3, "unknown action", SafeLastError()));
        return 0;
    }

    static string GetString(JsonElement obj, string name, string def)
    {
        if (obj.ValueKind == JsonValueKind.Undefined || obj.ValueKind == JsonValueKind.Null)
            return def;
        return obj.TryGetProperty(name, out var v) ? (v.GetString() ?? def) : def;
    }

    static int GetInt(JsonElement obj, string name, int def)
    {
        if (obj.ValueKind == JsonValueKind.Undefined || obj.ValueKind == JsonValueKind.Null)
            return def;
        if (!obj.TryGetProperty(name, out var v))
            return def;
        try
        {
            return v.ValueKind == JsonValueKind.Number ? v.GetInt32() : int.Parse(v.GetString() ?? def.ToString());
        }
        catch { return def; }
    }
}
