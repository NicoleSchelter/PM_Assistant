# PM Analysis Tool - Interactive Mode Demo

The PM Analysis Tool now features an **Interactive Mode** that provides a guided, dialog-based experience for analyzing project management documents.

## 🚀 How to Launch Interactive Mode

### Method 1: Default Interactive Mode
When you run the tool without any parameters, it automatically starts in interactive mode:

```bash
python main_entry.py
```

### Method 2: Explicit Interactive Command
You can explicitly request interactive mode:

```bash
python main_entry.py interactive
```

### Method 3: Direct CLI Access
You can also access interactive mode directly:

```bash
python ui/cli/main.py interactive
```

## 🎯 Interactive Workflow

The interactive mode guides you through a complete analysis workflow:

### Step 1: Welcome & Initialization
- 🎨 Displays a welcome banner
- ⚙️ Initializes the PM Analysis Engine
- ✅ Confirms successful setup

### Step 2: Project Repository Selection
- 📂 Shows current directory as default
- ❓ Asks if you want to use current directory
- 📝 Allows manual path entry if needed
- ✅ Validates directory exists and is accessible

### Step 3: File Discovery & Display
- 🔍 Scans for project management documents
- 📋 Displays found files in a formatted table showing:
  - 📄 File names
  - 📊 File types (MD, XLSX, MPP, etc.)
  - 💾 File sizes
  - ✅ Readability status

### Step 4: Mode Detection & Recommendation
- 🎯 Analyzes available documents
- 🤖 Recommends optimal operation mode
- 📊 Shows confidence percentage
- 💭 Explains reasoning
- ✅ Lists available documents
- ⚠️ Lists missing documents
- 🔧 Allows mode override

### Step 5: Operation Mode Selection
Interactive selection between:

1. **📋 Document Check** - Verify required documents are present
2. **📊 Status Analysis** - Extract and analyze project data  
3. **📚 Learning Module** - Access PM best practices

### Step 6: Output Format Selection
Choose one or more output formats:

- **📝 Markdown** - Human-readable text reports
- **📊 Excel** - Structured data in spreadsheet format
- **💻 Console** - Display results in terminal only

### Step 7: Analysis Execution
- ⚡ Real-time progress display with spinners
- 📈 Progress bars for each phase
- ⏱️ Elapsed time tracking
- 🎯 Phase-by-phase status updates

### Step 8: Results Display
- 🎉 Success/failure status with visual indicators
- ⏱️ Execution duration
- 📊 Summary statistics
- 📋 Generated reports list with file paths

### Step 9: Next Steps Recommendations
Based on analysis results, suggests:

- 🔧 **Document Check Mode**: Create missing documents, run status analysis
- 📊 **Status Analysis Mode**: Address risks, update stakeholders
- ⚠️ **Any Errors**: Review and fix issues

### Step 10: Action Selection
Choose what to do next:

1. **🔄 Run Different Analysis Mode** - Restart with different settings
2. **📁 Analyze Different Project** - Switch to another project
3. **🔍 View Detailed Results** - See comprehensive analysis data
4. **🚪 Exit** - End the session

## 📱 User Experience Features

### Visual Enhancements
- 🎨 Rich console formatting with colors and icons
- 📊 Beautiful tables for data display
- 📦 Bordered panels for important information
- ✨ Progress bars and spinners for feedback

### Interactive Elements
- ❓ Yes/No prompts for decision points
- 📝 Text input for custom paths
- 🔢 Numbered choice menus
- ⏰ Real-time progress updates

### Error Handling
- 🛡️ Graceful error handling with user-friendly messages
- 🔄 Retry options for recoverable errors
- ⌨️ Ctrl+C handling for clean exit
- 📝 Clear error descriptions

## 🔄 Backward Compatibility

The traditional CLI mode still works exactly as before:

```bash
# Traditional CLI usage still works
python main_entry.py --mode status-analysis --project-path ./my-project --output-format markdown

# All existing commands and options are preserved
python main_entry.py analyze --mode document-check --verbose
python main_entry.py detect-mode --project-path ./project
python main_entry.py list-files --project-path ./project
python main_entry.py status
```

## 🎯 When to Use Each Mode

### Use Interactive Mode When:
- 👥 New users learning the tool
- 🔍 Exploring a new project
- ❓ Unsure about optimal settings
- 🎨 Want guided experience
- 📊 Need to see results and decide next steps

### Use CLI Mode When:
- 🤖 Automating with scripts
- 🔄 Batch processing multiple projects
- ⚡ Quick analysis with known parameters
- 🔧 Integration with other tools
- 📝 Non-interactive environments

## 💡 Example Interactive Session

```
╭─── Interactive Analysis ───╮
│ Welcome to PM Analysis Tool │
│ Interactive Mode           │
╰────────────────────────────╯

✓ Engine initialized successfully

📂 Project Repository Selection
Current directory: /my-projects/webapp
Use current directory as project root? [Y/n]: y
✓ Selected project directory: /my-projects/webapp

🔍 Scanning project: /my-projects/webapp

  Discovered Project Files (12 total)
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 📄 File                                          ┃ 📋 Type                                          ┃ 💾 Size                                          ┃ ✅ Status                                         ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Project Charter.md                               │ MD                                                │ 4.2 KB                                           │ ✅ Ready                                          │
│ Risk Management Plan.md                          │ MD                                                │ 8.1 KB                                           │ ✅ Ready                                          │
│ Stakeholder Register.xlsx                        │ XLSX                                              │ 15.3 KB                                          │ ✅ Ready                                          │
└──────────────────────────────────────────────────┴───────────────────────────────────────────────────┴───────────────────────────────────────────────────┴───────────────────────────────────────────────────┘

🎯 Analyzing project and recommending operation mode...

╭──────── Mode Analysis Results ────────╮
│ 🎯 Recommended Mode: Status Analysis  │
│ 📊 Confidence: 89%                    │
│ 💭 Reasoning: Multiple structured     │
│ documents found with project data     │
╰───────────────────────────────────────╯

✅ Available Documents:
  • Project Charter
  • Risk Management Plan
  • Stakeholder Register

Use recommended mode (status-analysis)? [Y/n]: y
✓ Selected mode: status-analysis

📄 Output Format Selection
Generate 📝 Markdown - Human-readable text reports? [Y/n]: y
Generate 📊 Excel - Structured data in spreadsheet format? [y/N]: y
Generate 💻 Console - Display results in terminal only? [y/N]: n
✓ Selected formats: markdown, excel

🚀 Running PM Analysis...
⚡ Analysis Complete!

🎉 Analysis Completed Successfully!
✅ Status: Success
⏱️ Duration: 2.34 seconds
🎯 Operation: status_analysis

📊 Generated Reports
  ✅ Markdown: reports/analysis_report_20250823_141512.md
  ✅ Excel: reports/analysis_report_20250823_141512.xlsx

🎯 Recommended Next Steps
  1. ⚠️ Address identified risks and issues
  2. 📈 Update project stakeholders with analysis results

What would you like to do next?
  1. 🔄 Run different analysis mode
  2. 📁 Analyze different project  
  3. 📊 View detailed results
  4. 🚪 Exit

Select action (1-4) [4]: 4

👋 Thank you for using PM Analysis Tool!
```

## 🛠️ Technical Details

The interactive mode is implemented in the UI layer following the 4-layer architecture:
- **Location**: `ui/cli/main.py`
- **Function**: `_run_interactive_mode()`
- **Dependencies**: Rich library for enhanced console output
- **Integration**: Seamlessly works with existing Logic, Service, and Data layers

The implementation maintains clean separation of concerns and can be easily extended with additional interactive features.