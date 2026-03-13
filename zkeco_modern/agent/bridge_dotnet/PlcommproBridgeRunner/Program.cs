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

    [DllImport("plcommpro.dll", EntryPoint = "GetRTLog", CallingConvention = CallingConvention.StdCall)]
    public static extern int GetRTLog(int handle, IntPtr outBuf, int outLen);

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

sealed class BridgeResponse
{
    public bool ok { get; set; }
    public int result { get; set; }
    public string data { get; set; } = "";
    public int last_error { get; set; }
    public string action { get; set; } = "";
    public string action_alias { get; set; } = "";
    public string dll_path_used { get; set; } = "";
    public string note { get; set; } = "";
    public Dictionary<string, object?> meta { get; set; } = new(StringComparer.OrdinalIgnoreCase);
}

readonly record struct BridgeAction(string CanonicalAction, string ActionAlias);

class Program
{
    static int Main(string[] args)
    {
        string requestJson = "";
        string requestFile = "";
        string dllPath = "";
        string rawAction = "";
        var actionSpec = new BridgeAction("", "");
        try
        {
            for (int i = 0; i < args.Length; i++)
            {
                if (args[i] == "--request-file" && i + 1 < args.Length)
                {
                    requestFile = args[i + 1] ?? "";
                    i++;
                    continue;
                }
                if (args[i] == "--request" && i + 1 < args.Length)
                {
                    requestJson = args[i + 1] ?? "";
                    i++;
                    continue;
                }
            }

            if (!string.IsNullOrWhiteSpace(requestFile))
            {
                requestJson = File.ReadAllText(requestFile);
            }

            if (string.IsNullOrWhiteSpace(requestJson))
            {
                Write(CreateResponse(false, -1, "missing --request or --request-file", 0, "", "", "", "missing request payload"));
                return 2;
            }

            using var doc = JsonDocument.Parse(requestJson);
            var root = doc.RootElement;

            rawAction = root.TryGetProperty("action", out var a) ? (a.GetString() ?? "") : "";
            actionSpec = NormalizeAction(rawAction);
            string action = actionSpec.CanonicalAction;

            dllPath = root.TryGetProperty("dll_path", out var dp) ? (dp.GetString() ?? "") : "";

            PlcommproNative.EnsureLoaded(string.IsNullOrWhiteSpace(dllPath) ? null : dllPath);

            // Fast sanity check: only load the DLL and exit.
            if (action == "load_only")
            {
                Write(CreateResponse(true, 1, "loaded", 0, action, actionSpec.ActionAlias, dllPath, "bridge loaded"));
                return 0;
            }

            if (action == "search_device")
            {
                string? address = root.TryGetProperty("address", out var ad) ? ad.GetString() : null;
                return HandleSearchDevice(address, actionSpec, dllPath);
            }

            if (action == "modify_ip")
            {
                string payload = root.TryGetProperty("payload", out var p) ? (p.GetString() ?? "") : "";
                string? address = root.TryGetProperty("address", out var ad) ? ad.GetString() : null;
                return HandleModifyIp(payload, address, actionSpec, dllPath);
            }

            // Remaining actions require connected handle.
            var comm = root.TryGetProperty("comminfo", out var ci) ? ci : default;
            int handle = Connect(comm);
            if (handle <= 0)
            {
                int lastErr = SafeLastError();
                Write(CreateResponse(false, handle, "connect failed", lastErr, action, actionSpec.ActionAlias, dllPath, "connect failed", BuildConnectionMeta(root, comm)));
                return 0;
            }

            try
            {
                return action switch
                {
                    "connect_only" => HandleConnectOnly(handle, root, actionSpec, dllPath),
                    "get_options" => HandleGetOptions(handle, root, actionSpec, dllPath),
                    "set_options" => HandleSetOptions(handle, root, actionSpec, dllPath),
                    "get_rtlog" => HandleGetRtlog(handle, root, actionSpec, dllPath),
                    "data_count" => HandleDataCount(handle, root, actionSpec, dllPath),
                    "query_data" => HandleQueryData(handle, root, actionSpec, dllPath),
                    "delete_data" => HandleDeleteData(handle, root, actionSpec, dllPath),
                    "set_data" => HandleSetData(handle, root, actionSpec, dllPath),
                    "enable_device" => HandleEnableDevice(handle, root, actionSpec, dllPath),
                    "control_device" => HandleControlDevice(handle, root, actionSpec, dllPath, operation: 1),
                    "cancel_alarm" => HandleControlDevice(handle, root, actionSpec, dllPath, operation: 2),
                    "reboot" => HandleControlDevice(handle, root, actionSpec, dllPath, operation: 3),
                    "control_normal_open" => HandleControlDevice(handle, root, actionSpec, dllPath, operation: 4),
                    _ => UnknownAction(actionSpec, dllPath)
                };
            }
            finally
            {
                try { PlcommproNative.Disconnect(handle); } catch { }
            }
        }
        catch (Exception ex)
        {
            Write(CreateResponse(false, -500, $"exception: {ex.Message}", SafeLastError(), actionSpec.CanonicalAction, actionSpec.ActionAlias, dllPath, "unhandled exception"));
            return 0;
        }
    }

    static BridgeAction NormalizeAction(string rawAction)
    {
        string alias = (rawAction ?? "").Trim().ToLowerInvariant();
        return alias switch
        {
            "load_only" => new BridgeAction("load_only", alias),
            "connect" or "connect_only" => new BridgeAction("connect_only", alias),
            "get_options" or "get_device_options" or "option_read" or "read_controller_params" or "identify_controller" => new BridgeAction("get_options", alias),
            "set_options" or "set_device_options" or "option_write" or "write_controller_params" or "sync_time" => new BridgeAction("set_options", alias),
            "get_rtlog" or "rtlog_read" or "real_log" or "read_live_events" => new BridgeAction("get_rtlog", alias),
            "query_data" => new BridgeAction("query_data", alias),
            "get_transaction" or "transaction_read" or "transaction_query" => new BridgeAction("query_data", "get_transaction"),
            "data_count" or "get_data_count" or "getdatacount" or "count_data" => new BridgeAction("data_count", alias),
            "delete_data" or "delete_device_data" => new BridgeAction("delete_data", alias),
            "set_data" or "set_device_data" or "update_data" => new BridgeAction("set_data", alias),
            "enable_device" => new BridgeAction("enable_device", alias),
            "control_device" or "door_relay" or "door_open" or "door_close" => new BridgeAction("control_device", alias),
            "cancel_alarm" or "door_cancel_alarm" or "cancelwarning" => new BridgeAction("cancel_alarm", alias),
            "reboot" or "reboot_controller" or "reboot_device" => new BridgeAction("reboot", alias),
            "control_normal_open" or "set_normal_open" or "normal_open" or "control_normal_close" or "clear_normal_open" or "normal_close" => new BridgeAction("control_normal_open", alias),
            "search_device" or "search_device_udp" or "udp_discovery" => new BridgeAction("search_device", alias),
            "modify_ip" or "modify_ip_udp" or "change_ip" or "udp_modify_ip" => new BridgeAction("modify_ip", alias),
            _ => new BridgeAction(alias, alias),
        };
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

    static BridgeResponse CreateResponse(
        bool ok,
        int result,
        string data,
        int lastError,
        string action,
        string actionAlias,
        string dllPathUsed,
        string note = "",
        Dictionary<string, object?>? meta = null)
    {
        return new BridgeResponse
        {
            ok = ok,
            result = result,
            data = data ?? "",
            last_error = lastError,
            action = action ?? "",
            action_alias = actionAlias ?? "",
            dll_path_used = dllPathUsed ?? "",
            note = note ?? "",
            meta = meta ?? new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase),
        };
    }

    static Dictionary<string, object?> BuildConnectionMeta(JsonElement root, JsonElement comm)
    {
        var meta = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
        if (comm.ValueKind != JsonValueKind.Undefined && comm.ValueKind != JsonValueKind.Null)
        {
            meta["comm_type"] = GetInt(comm, "comm_type", 1);
            meta["protocol"] = GetString(comm, "protocol", "TCP");
            meta["ipaddress"] = GetString(comm, "ipaddress", "");
            meta["ip_port"] = GetInt(comm, "ip_port", 4370);
            meta["timeout"] = GetInt(comm, "timeout", 3000);
            meta["password_present"] = !string.IsNullOrWhiteSpace(GetString(comm, "password", ""));
            meta["com_port"] = GetString(comm, "com_port", "");
            meta["com_address"] = GetInt(comm, "com_address", 1);
        }
        return meta;
    }

    static Dictionary<string, object?> BuildTextMeta(string data)
    {
        var meta = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase);
        string normalized = (data ?? "").Replace("\r\n", "\n").Replace('\r', '\n');
        var rawLines = normalized.Split('\n');
        var lines = new List<string>();
        foreach (var raw in rawLines)
        {
            var line = (raw ?? "").Trim();
            if (line.Length > 0)
                lines.Add(line);
        }

        meta["line_count"] = lines.Count;
        meta["preview"] = lines.Count == 0 ? "" : string.Join(" | ", lines.GetRange(0, Math.Min(3, lines.Count)));
        if (lines.Count > 0)
        {
            string first = lines[0];
            bool hasHeader = first.Contains(',') && first.IndexOf('=') < 0 && LooksLikeHeader(first);
            meta["has_header"] = hasHeader;
            meta["first_line"] = first;
        }
        return meta;
    }

    static Dictionary<string, string> ParseOptionPairs(string data)
    {
        var pairs = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
        string normalized = (data ?? "").Replace("\r\n", "\n").Replace('\r', '\n');
        foreach (var line in normalized.Split('\n'))
        {
            foreach (var part in line.Split(new[] { ',', '\t' }, StringSplitOptions.RemoveEmptyEntries))
            {
                var chunk = (part ?? "").Trim();
                int eq = chunk.IndexOf('=');
                if (eq <= 0)
                    continue;
                var key = chunk.Substring(0, eq).Trim();
                var value = chunk.Substring(eq + 1).Trim();
                if (key.Length > 0)
                    pairs[key] = value;
            }
        }
        return pairs;
    }

    static List<Dictionary<string, string>> ParseSearchDeviceRecords(string data)
    {
        var records = new List<Dictionary<string, string>>();
        string normalized = (data ?? "").Replace("\0", "").Replace("\r\n", "\n").Replace('\r', '\n');
        foreach (var rawLine in normalized.Split('\n'))
        {
            var line = (rawLine ?? "").Trim();
            if (line.Length == 0 || !line.Contains('='))
                continue;
            var parsed = ParseOptionPairs(line);
            if (parsed.Count == 0)
                continue;
            records.Add(new Dictionary<string, string>(parsed, StringComparer.OrdinalIgnoreCase));
        }
        return records;
    }

    static bool LooksLikeHeader(string line)
    {
        foreach (var part in line.Split(','))
        {
            bool hasLetter = false;
            foreach (char ch in part)
            {
                if (char.IsLetter(ch) || ch == '~')
                {
                    hasLetter = true;
                    break;
                }
            }
            if (hasLetter)
                return true;
        }
        return false;
    }

    static int HandleSearchDevice(string? address, BridgeAction action, string dllPath)
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
            var meta = BuildTextMeta(data);
            meta["address"] = addr;
            meta["protocol"] = "UDP";
            meta["device_records"] = ParseSearchDeviceRecords(data);
            meta["device_record_count"] = ((List<Dictionary<string, string>>)meta["device_records"]!).Count;
            Write(CreateResponse(ret >= 0, ret, data, lastErr, action.CanonicalAction, action.ActionAlias, dllPath, "search_device completed", meta));
            return 0;
        }
        finally
        {
            if (hOut.IsAllocated) hOut.Free();
            if (hProto.IsAllocated) hProto.Free();
            if (hAddr.IsAllocated) hAddr.Free();
        }
    }

    static int HandleModifyIp(string payload, string? address, BridgeAction action, string dllPath)
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
            var meta = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase)
            {
                ["address"] = addr,
                ["protocol"] = "UDP",
                ["payload"] = payload,
                ["payload_length"] = payload.Length,
            };
            Write(CreateResponse(ret >= 0, ret, "", lastErr, action.CanonicalAction, action.ActionAlias, dllPath, "modify_ip completed", meta));
            return 0;
        }
        finally
        {
            if (hProto.IsAllocated) hProto.Free();
            if (hAddr.IsAllocated) hAddr.Free();
            if (hPayload.IsAllocated) hPayload.Free();
        }
    }

    static int HandleConnectOnly(int handle, JsonElement root, BridgeAction action, string dllPath)
    {
        // If we reached here, Connect() succeeded.
        var comm = root.TryGetProperty("comminfo", out var ci) ? ci : default;
        Write(CreateResponse(true, handle, "connected", SafeLastError(), action.CanonicalAction, action.ActionAlias, dllPath, "connected", BuildConnectionMeta(root, comm)));
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

    static int HandleGetOptions(int handle, JsonElement root, BridgeAction action, string dllPath)
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
            var meta = BuildTextMeta(data);
            meta["items"] = items;
            meta["option_pairs"] = ParseOptionPairs(data);
            Write(CreateResponse(ret >= 0, ret, data, lastErr, action.CanonicalAction, action.ActionAlias, dllPath, "get_options completed", meta));
            return 0;
        }
        finally
        {
            if (hOut.IsAllocated) hOut.Free();
            if (hItems.IsAllocated) hItems.Free();
        }
    }

    static int HandleSetOptions(int handle, JsonElement root, BridgeAction action, string dllPath)
    {
        string items = root.TryGetProperty("items", out var it) ? (it.GetString() ?? "") : "";
        GCHandle hItems = default;
        IntPtr pItems = Util.AllocZ(items, out hItems);
        try
        {
            int ret = PlcommproNative.SetDeviceParam(handle, pItems);
            int lastErr = SafeLastError();
            var meta = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase)
            {
                ["items"] = items,
                ["option_pairs"] = ParseOptionPairs(items),
            };
            Write(CreateResponse(ret >= 0, ret, "", lastErr, action.CanonicalAction, action.ActionAlias, dllPath, "set_options completed", meta));
            return 0;
        }
        finally
        {
            if (hItems.IsAllocated) hItems.Free();
        }
    }

    static int HandleDataCount(int handle, JsonElement root, BridgeAction action, string dllPath)
    {
        string table = root.TryGetProperty("table", out var t) ? (t.GetString() ?? "") : "";
        string filter = root.TryGetProperty("filter", out var fl) ? (fl.GetString() ?? "") : "";
        string option = root.TryGetProperty("option", out var op) ? (op.GetString() ?? "") : "";
        GCHandle hTable = default, hFilter = default, hOpt = default;
        IntPtr pTable = Util.AllocZ(table, out hTable);
        IntPtr pFilter = Util.AllocZ(filter, out hFilter);
        IntPtr pOpt = Util.AllocZ(option, out hOpt);
        try
        {
            int ret = PlcommproNative.GetDeviceDataCount(handle, pTable, pFilter, pOpt);
            int lastErr = SafeLastError();
            var meta = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase)
            {
                ["table"] = table,
                ["filter"] = filter,
                ["option"] = option,
            };
            Write(CreateResponse(ret >= 0, ret, "", lastErr, action.CanonicalAction, action.ActionAlias, dllPath, "data_count completed", meta));
            return 0;
        }
        finally
        {
            if (hTable.IsAllocated) hTable.Free();
            if (hFilter.IsAllocated) hFilter.Free();
            if (hOpt.IsAllocated) hOpt.Free();
        }
    }

    static int HandleQueryData(int handle, JsonElement root, BridgeAction action, string dllPath)
    {
        string table = root.TryGetProperty("table", out var t) ? (t.GetString() ?? "") : "";
        if (string.IsNullOrWhiteSpace(table) && action.ActionAlias == "get_transaction")
            table = "transaction";
        string fields = root.TryGetProperty("fields", out var f) ? (f.GetString() ?? "*") : "*";
        string filter = root.TryGetProperty("filter", out var fl) ? (fl.GetString() ?? "") : "";
        string option = root.TryGetProperty("option", out var op) ? (op.GetString() ?? "") : "";
        if (string.IsNullOrWhiteSpace(option) && action.ActionAlias == "get_transaction")
            option = "NewRecord";
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
            var meta = BuildTextMeta(data);
            meta["table"] = table;
            meta["fields"] = fields;
            meta["filter"] = filter;
            meta["option"] = option;
            meta["buffer_len"] = bufLen;
            if (table.Equals("transaction", StringComparison.OrdinalIgnoreCase) || table.Equals("rtlog", StringComparison.OrdinalIgnoreCase) || action.ActionAlias == "get_transaction")
                meta["data_kind"] = "event_rows";
            else if (table.Equals("user", StringComparison.OrdinalIgnoreCase))
                meta["data_kind"] = "user_rows";
            Write(CreateResponse(ret >= 0, ret, data, lastErr, action.CanonicalAction, action.ActionAlias, dllPath, "query_data completed", meta));
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

    static int HandleGetRtlog(int handle, JsonElement root, BridgeAction action, string dllPath)
    {
        int bufLen = GetInt(root, "buffer_len", 65536);
        if (bufLen < 4096) bufLen = 4096;
        if (bufLen > 1024 * 1024) bufLen = 1024 * 1024;

        byte[] outBuf = ArrayPool<byte>.Shared.Rent(bufLen);
        Array.Clear(outBuf, 0, bufLen);
        GCHandle hOut = default;
        try
        {
            hOut = GCHandle.Alloc(outBuf, GCHandleType.Pinned);
            int ret = PlcommproNative.GetRTLog(handle, hOut.AddrOfPinnedObject(), bufLen);
            int lastErr = SafeLastError();
            string data = "";
            if (ret >= 0)
            {
                data = Util.FromLatin1Z(outBuf);
            }
            var meta = BuildTextMeta(data);
            meta["buffer_len"] = bufLen;
            meta["data_kind"] = "rtlog";
            Write(CreateResponse(ret >= 0, ret, data, lastErr, action.CanonicalAction, action.ActionAlias, dllPath, "get_rtlog completed", meta));
            return 0;
        }
        finally
        {
            if (hOut.IsAllocated) hOut.Free();
            ArrayPool<byte>.Shared.Return(outBuf);
        }
    }

    static int HandleDeleteData(int handle, JsonElement root, BridgeAction action, string dllPath)
    {
        string table = root.TryGetProperty("table", out var t) ? (t.GetString() ?? "") : "";
        string filter = root.TryGetProperty("filter", out var fl) ? (fl.GetString() ?? "") : "";
        string option = root.TryGetProperty("option", out var op) ? (op.GetString() ?? "") : "";

        GCHandle hTable = default, hFilter = default, hOpt = default;
        IntPtr pTable = Util.AllocZ(table, out hTable);
        IntPtr pFilter = Util.AllocZ(filter, out hFilter);
        IntPtr pOpt = Util.AllocZ(option, out hOpt);

        try
        {
            int ret = PlcommproNative.DeleteDeviceData(handle, pTable, pFilter, pOpt);
            int lastErr = SafeLastError();
            var meta = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase)
            {
                ["table"] = table,
                ["filter"] = filter,
                ["option"] = option,
            };
            Write(CreateResponse(ret >= 0, ret, "", lastErr, action.CanonicalAction, action.ActionAlias, dllPath, "delete_data completed", meta));
            return 0;
        }
        finally
        {
            if (hTable.IsAllocated) hTable.Free();
            if (hFilter.IsAllocated) hFilter.Free();
            if (hOpt.IsAllocated) hOpt.Free();
        }
    }

    static int HandleSetData(int handle, JsonElement root, BridgeAction action, string dllPath)
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
            var meta = BuildTextMeta(data);
            meta["table"] = table;
            meta["option"] = option;
            meta["data_kind"] = "set_data_payload";
            Write(CreateResponse(ret >= 0, ret, "", lastErr, action.CanonicalAction, action.ActionAlias, dllPath, "set_data completed", meta));
            return 0;
        }
        finally
        {
            if (hTable.IsAllocated) hTable.Free();
            if (hData.IsAllocated) hData.Free();
            if (hOpt.IsAllocated) hOpt.Free();
        }
    }

    static int HandleEnableDevice(int handle, JsonElement root, BridgeAction action, string dllPath)
    {
        int enable = GetInt(root, "enable", 1);
        try
        {
            int ret = PlcommproNative.EnableDevice(handle, enable);
            int lastErr = SafeLastError();
            var meta = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase)
            {
                ["enable"] = enable,
            };
            Write(CreateResponse(ret >= 0, ret, "", lastErr, action.CanonicalAction, action.ActionAlias, dllPath, "enable_device completed", meta));
            return 0;
        }
        catch
        {
            Write(CreateResponse(false, -1, "EnableDevice not available", SafeLastError(), action.CanonicalAction, action.ActionAlias, dllPath, "EnableDevice not available"));
            return 0;
        }
    }

    static int HandleControlDevice(int handle, JsonElement root, BridgeAction action, string dllPath, int operation)
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
        if (operation == 1)
        {
            if (action.ActionAlias == "door_open")
            {
                if (index == 0) index = 1;
                state = 1;
            }
            else if (action.ActionAlias == "door_close")
            {
                if (index == 0) index = 1;
                state = 0;
            }
        }
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
            if (action.ActionAlias is "control_normal_close" or "clear_normal_open" or "normal_close")
                state = 0;
            index = state;
            state = 0;
        }

        GCHandle hRes = default;
        IntPtr pRes = Util.AllocZ(reserved, out hRes);
        try
        {
            int ret = PlcommproNative.ControlDevice(handle, operation, door, index, state, time, pRes);
            int lastErr = SafeLastError();
            var meta = new Dictionary<string, object?>(StringComparer.OrdinalIgnoreCase)
            {
                ["operation"] = operation,
                ["operation_name"] = operation switch
                {
                    1 => "control_device",
                    2 => "cancel_alarm",
                    3 => "reboot",
                    4 => "control_normal_open",
                    _ => "unknown",
                },
                ["door"] = door,
                ["index"] = index,
                ["state"] = state,
                ["time"] = time,
                ["reserved"] = reserved,
            };
            Write(CreateResponse(ret >= 0, ret, "", lastErr, action.CanonicalAction, action.ActionAlias, dllPath, "control operation completed", meta));
            return 0;
        }
        finally
        {
            if (hRes.IsAllocated) hRes.Free();
        }
    }

    static int UnknownAction(BridgeAction action, string dllPath)
    {
        Write(CreateResponse(false, -3, "unknown action", SafeLastError(), action.CanonicalAction, action.ActionAlias, dllPath, "unknown action"));
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
