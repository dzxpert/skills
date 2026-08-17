---
name: ida-pro-mcp
description: Comprehensive workflow guide and tool reference for reverse engineering binaries using IDA Pro MCP. Use when analyzing executables, DLLs, firmware, or malware in IDA Pro; performing binary triage, decompilation, type recovery, structure creation, call graph & data flow analysis, database modifications, signature generation, or multi-database / multi-instance concurrent binary analysis.
---

# IDA Pro MCP Agent Workflow & Tool Reference

`ida-pro-mcp` bridges IDA Pro (GUI & headless `idalib`) with LLM agents via Model Context Protocol. This guide details optimal agent strategies, pipeline stages, query syntaxes, tool usage, and **multi-instance / multi-binary management** to maximize analysis quality while avoiding context fragmentation and session collisions.

---

## 🚨 Critical Agent Guardrails

1. **NEVER convert number bases manually**:
   - Always use `int_convert` for hex ↔ decimal ↔ byte conversions. Manual calculation by LLMs introduces subtle bugs.
2. **Always start with `survey_binary()`**:
   - Do NOT run `list_funcs`, `imports`, or `find_regex` individually for initial triage. `survey_binary()` aggregates metadata, segment maps, imports by security category, top strings, and key functions in **one single call**.
3. **Use Composite & Query tools over raw loops**:
   - Prefer `analyze_function`, `analyze_component`, `trace_data_flow`, `diff_before_after`, and `func_query` / `entity_query` over multiple individual calls.
4. **Specify `database` session ID in Headless & Multi-Instance mode**:
   - When using `idalib-mcp` or working with multiple open binaries, **every tool call must pass `database="<session_id>"`** returned by `idb_open`.
5. **Verify changes using `diff_before_after`**:
   - When renaming functions or setting types, use `diff_before_after` to verify that decompilation quality improved without issuing separate `rename` + `decompile` requests.

---

## 🔀 Multi-Instance & Multi-Binary Operations (`idalib-mcp`)

`idalib-mcp` supports **concurrent multi-database execution**. The supervisor process runs independent worker processes in parallel for each open binary (or connects to open GUI instances), allowing agents to analyze multiple binaries (e.g., `app.exe` and `helper.dll`, or main binary vs patched binary) simultaneously without closing or context-switching.

### How Multi-Instance Routing Works
1. **Open each binary**: Call `idb_open(input_path, preferred_session_id="...")` for each file.
2. **Track session IDs**: Each call returns a session handle (e.g., `"app"`, `"dll"`).
3. **Explicit Call Targeting**: Pass `database="<session_id>"` with every subsequent tool call.

```
                    ┌─────────────────────────┐
                    │   idalib-mcp Supervisor │
                    └────────────┬────────────┘
                                 │
           ┌─────────────────────┴─────────────────────┐
           ▼                                           ▼
┌──────────────────────┐                    ┌──────────────────────┐
│  Worker Session: app │                    │ Worker Session: dll  │
│  (app.exe IDB)       │                    │ (helper.dll IDB)     │
└──────────────────────┘                    └──────────────────────┘
```

### Multi-Instance Workflow Example
```python
# 1. Open both target binaries
idb_open("C:\\analysis\\target.exe", preferred_session_id="target_app")
idb_open("C:\\analysis\\core_lib.dll", preferred_session_id="core_lib")

# 2. Query sessions to verify active workers
sessions = idb_list()

# 3. Perform side-by-side analysis without switching databases
main_code = decompile("main", database="target_app")
dll_export = decompile("ExportedCryptoInit", database="core_lib")

# 4. Trace data flow across boundary
trace_data_flow("0x401000", direction="forward", database="target_app")

# 5. Clean up when finished
idb_close(database="core_lib", save=True)
```

---

## 🔄 Standard Reverse Engineering Agent Pipeline

Follow this 5-stage pipeline for structured, reliable binary reverse engineering:

```
┌─────────────────────────────────────────────────────────┐
│ Stage 1: Triage & Discovery                             │
│ survey_binary() ──► Metadata, Entrypoints, Imports      │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│ Stage 2: Target Selection & Decompilation               │
│ analyze_function() / analyze_component()                │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│ Stage 3: Type Recovery & Database Refactoring           │
│ declare_type() ──► type_apply_batch() ──► diff_before_after()
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│ Stage 4: Data Flow & Cross-Reference Tracing            │
│ trace_data_flow() ──► xrefs_to_field()                  │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│ Stage 5: Signatures & Documentation                     │
│ make_signature() ──► set_comments() ──► idb_save()      │
└──────────────────────────┘
```

### Stage 1: Triage & Discovery
- **Goal**: Understand architecture, entry points, security-critical imports, strings, and primary logic drivers.
- **Tools**:
  - `survey_binary(detail_level="standard", database="...")` (or `"minimal"` for binaries >10k functions).
  - `idb_open(input_path, mode="prefer_headless")` if operating headlessly.

### Stage 2: Function & Component Deep Dive
- **Goal**: Analyze decompiled C pseudocode, control flow, callers/callees, and local constants.
- **Tools**:
  - `analyze_function(addr="0x401000", include_asm=False, database="...")`: Gives decompilation, strings, constants, callees/callers, and cyclomatic complexity.
  - `analyze_component(addrs=["0x401000", "0x401500"], database="...")`: Analyzes a group of functions as a module, returning shared global accesses and internal call graphs.

### Stage 3: Type System & Struct Recovery
- **Goal**: Declare C structures, parse prototypes, rename variables, and update type definitions.
- **Tools**:
  - `declare_type(decls="struct Header { int magic; int len; };", database="...")`: Registers struct or typedef in the local type library.
  - `diff_before_after(addr="main", action="rename_func", action_args={"name": "process_packet"}, database="...")`: Applies rename/type change and returns before/after decompilation side-by-side.
  - `type_apply_batch(items=[{"addr": "0x401000", "type": "int __fastcall(Header *hdr)"}], database="...")`: Applies multiple function signatures in bulk.
  - `search_structs(query="Header", database="...")` / `read_struct(name="Header", database="...")`: Inspects existing structure layouts.

### Stage 4: Tracing & Data Flow Analysis
- **Goal**: Trace propagation of key variables, crypto keys, or network buffers across call boundaries.
- **Tools**:
  - `trace_data_flow(addr="0x403004", direction="forward", max_depth=5, database="...")`: Automatically walks xrefs forward or backward across multiple hops.
  - `xrefs_to_field(queries=["Header.magic"], database="...")`: Finds all instructions referencing specific structure fields.

### Stage 5: Signature Generation & Final Reporting
- **Goal**: Extract pattern signatures for YARA/hooking and persist findings.
- **Tools**:
  - `make_signature(addrs=["0x401000"], database="...")`: Generates shortest unique byte pattern signature with operand wildcarding.
  - `find_xref_signatures(addrs=["g_SecretKey"], database="...")`: Generates signatures for code instructions referencing data.
  - `set_comments(items=[{"addr": "0x401000", "comment": "Decrypts payload"}], database="...")`.
  - `idb_save(database="...")`: Saves database state.

---

## 🛠️ Complete MCP Tool Reference

### 1. Session & Triage Tools
| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `idb_open` | Open IDB/binary session | `input_path`, `mode`: `"prefer_headless"`, `"prefer_gui"`, `"force_headless"`, `"force_gui"`, `preferred_session_id` |
| `idb_list` | List active IDB sessions & workers | None |
| `idb_close` | Close & save worker session | `database`, `save`: `True`/`False` |
| `idb_save` | Flush IDB database to disk | `database` |
| `survey_binary` | Single-call binary triage & overview | `detail_level`: `"standard"` or `"minimal"`, `database` |
| `server_health` | Verify server RPC status | `database` |
| `int_convert` | Base conversions (hex, dec, ASCII, bytes) | `inputs`: `["0x41424344", 1094795588]` |

### 2. High-Level Composite & Workflow Tools
| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `analyze_function` | Compact function triage & pseudocode | `addr`, `include_asm` (default: `False`), `database` |
| `analyze_component` | Group function analysis & shared globals | `addrs`: list of addresses/names, `database` |
| `diff_before_after` | Apply rename/type/comment & compare decompile | `addr`, `action`: `"rename_func"` \| `"set_type"` \| `"set_comment"`, `action_args`, `database` |
| `trace_data_flow` | Multi-hop XREF data flow graph | `addr`, `direction`: `"forward"` \| `"backward"`, `max_depth`, `database` |

### 3. Query & Lookup Tools
| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `lookup_funcs` | Quick address/name function resolution | `queries`: list or string, `database` |
| `list_funcs` | List all functions (paginated) | `offset`, `count`, `query`, `database` |
| `func_query` | Query functions with filter expressions | `query`: `"name == 'main'"`, `"size > 500"`, `database` |
| `list_globals` | List global variables | `offset`, `count`, `query`, `database` |
| `entity_query` | Unified entity search (funcs, globals, types) | `query`: regex or search pattern, `database` |
| `imports` | List imported API symbols | `offset`, `count`, `database` |
| `imports_query` | Search imports by module/name | `query`: `"ws2_32"` or `"socket"`, `database` |
| `export_funcs` | List exported functions | `database` |
| `find_regex` | Search text/names with regex | `pattern`, `database` |
| `search_text` | Search disassembly text | `query`, `database` |
| `find_bytes` | Search raw byte patterns | `pattern`: `"48 8B 05 ?? ?? ?? ??"`, `database` |

### 4. Decompilation & Disassembly Tools
| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `decompile` | Hex-Rays pseudocode generation | `addr`, `database` |
| `disasm` | Full disassembly with stack frame | `addr`, `database` |
| `basic_blocks` | Control flow graph blocks | `addr`, `database` |
| `callees` | Get outgoing function calls | `addrs`, `database` |
| `xrefs_to` | Get incoming references | `addrs`, `database` |
| `xref_query` | Query xrefs with filtering | `to`, `type`, `database` |
| `callgraph` | Call graph tree from root | `addr`, `depth`, `database` |
| `insn_query` | Query assembly instructions | `addr` or range, `database` |
| `func_profile` | Execution profile / complexity metrics | `addr`, `database` |
| `analyze_batch` | Batch decompile multiple functions | `addrs`, `database` |

### 5. Type Engineering & Struct Tools
| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `declare_type` | Parse C declaration into type library | `decls`: C code string, `database` |
| `set_type` | Apply C type to variable/function | `addr`, `type`: C prototype string, `database` |
| `type_apply_batch` | Apply multiple types in bulk | `items`: `[{"addr": ..., "type": ...}]`, `database` |
| `type_query` | Search local type library | `query`: string, `database` |
| `type_inspect` | Detailed view of a type declaration | `name`, `database` |
| `read_struct` | Get struct field layout & offsets | `name`, `database` |
| `search_structs` | Search structs by name/field | `query`, `database` |
| `enum_upsert` | Create/update enum definition | `name`, `members`, `database` |
| `infer_types` | Trigger Hex-Rays type inference | `addr`, `database` |
| `stack_frame` | Inspect function stack variables | `addr`, `database` |
| `declare_stack` | Declare/modify stack variable | `addr`, `offset`, `name`, `type`, `database` |
| `delete_stack` | Remove stack variable | `addr`, `offset`, `database` |

### 6. Database Modification Tools
| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `rename` | Rename symbol at address | `addr`, `name`, `database` |
| `set_comments` | Set comment (asm & decompiler) | `items`: `[{"addr": ..., "comment": ...}]`, `database` |
| `append_comments` | Append to existing comment | `items`: `[{"addr": ..., "comment": ...}]`, `database` |
| `patch_asm` | Assemble and patch instruction | `items`: `[{"addr": ..., "asm": "nop"}], database` |
| `patch` | Patch raw bytes | `addr`, `data`: hex string, `database` |
| `put_int` | Write integer to memory | `addr`, `value`, `size`, `database` |
| `define_func` | Mark range as function | `items`: address or range, `database` |
| `define_code` | Convert bytes to code | `items`: address or list, `database` |
| `undefine` | Clear item to raw bytes | `items`: address or range, `database` |
| `force_recompile` | Invalidate Hex-Rays cfunc cache | `addr`, `database` |
| `set_op_type` | Change operand format (hex/dec/enum) | `addr`, `op_idx`, `type`, `database` |
| `make_data` | Convert bytes to data item | `addr`, `type_name`, `database` |
| `add_bookmark` | Set IDA bookmark | `addr`, `name`, `prefix`, `database` |

### 7. Signature Generation Tools
| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `make_signature` | Shortest unique signature for address | `addrs`, `format`: `"ida"` \| `"x64dbg"` \| `"mask"` \| `"bitmask"`, `database` |
| `make_signature_for_function` | Signature for function start | `addrs`, `format`, `database` |
| `make_signature_for_range` | Signature for fixed range | `start`, `end`, `format`, `database` |
| `find_xref_signatures` | Signatures for instructions referencing data | `addrs`, `top`: 5, `format`, `database` |

### 8. Python Execution & Fallback Tools
| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `py_eval` | Evaluate IDAPython expression | `expr`: string, `database` |
| `py_exec_file` | Execute IDAPython script file | `path`: script path, `database` |

---

## 🌐 MCP Resources Reference

Browse state directly via MCP resources without issuing tool calls:

| Resource URI | Description |
|--------------|-------------|
| `ida://idb/metadata` | File path, architecture, base address, hashes |
| `ida://idb/segments` | Memory segment layout and permissions (`rwx`) |
| `ida://idb/entrypoints` | Main entry points and TLS callbacks |
| `ida://cursor` | Current active UI cursor location & function |
| `ida://selection` | Current selection range in UI |
| `ida://types` | Complete list of local types |
| `ida://structs` | All struct and union names |
| `ida://struct/{name}` | Struct member offsets, sizes, and types |
| `ida://import/{name}` | Specific import details |
| `ida://export/{name}` | Specific export details |
| `ida://xrefs/from/{addr}` | Cross-references originating from address |

---

## 💡 Multi-Binary Analysis Prompt Template

```md
You are analyzing a target application and its supporting DLL concurrently using IDA Pro MCP:
1. Open both binaries:
   - `idb_open("C:\\path\\app.exe", preferred_session_id="app")`
   - `idb_open("C:\\path\\lib.dll", preferred_session_id="lib")`
2. Run `survey_binary(database="app")` and `survey_binary(database="lib")` to triage both databases.
3. Compare exported functions in `lib` against imported functions in `app`.
4. Decompile calling site in `app` with `decompile("0x401200", database="app")` and target function with `decompile("ExportedFunc", database="lib")`.
5. Use `diff_before_after(..., database="app")` when renaming or applying recovered structures.
6. When done, save both databases with `idb_save(database="app")` and `idb_save(database="lib")`.
```
