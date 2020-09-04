# JSgraph

This project contains the source code for the JSgraph system described in 

Bo Li, Phani Vadrevu, Kyu Hyung Lee, Roberto Perdisci. "JSgraph: Enabling Reconstruction of Web Attacks via Efficient Tracking of Live In-Browser JavaScript Executions". Network and Distributed System Security Symposium, NDSS 2018


## Build instructions (Ubuntu):
Note: these instructions assume that everything is downloaded into your home directory. If that is not the case, replace ~ and $HOME with your base path.

1. Setup Ubuntu 14 (VM recommended)
2. Update to latest Ubuntu 14 version: `sudo apt-get update && sudo apt-get dist-upgrade`, then reboot
3. Clone the chromium depot tools: `git clone https://chromium.googlesource.com/chromium/tools/depot_tools.git`
4. Add the depot_tools to your path: `export PATH="$PATH:$HOME/depot_tools”`
5. Pull down the chromium source code: `mkdir chromium && cd chromium && fetch --nohooks chromium`
6. Checkout the chromium 48.0.2528.1 source code: `cd src && git checkout tags/48.0.2528.1`
7. Change the src/DEPS opus line (123) to ref commit `5dca296833ce4941dceadf956ff0fb6fe59fe4e8` instead of `cae696156f1e60006e39821e79a1811ae1933c69` (which does not exist in the 3rd party opus repo)
8. Get the date this tag was released: `COMMIT_DATE=$(git log -n 1 --pretty=format:%ci)`
9. Checkout the depot_tools version that existed at the same date: `cd ~/depot_tools && git checkout $(git rev-list -n 1 --before="$COMMIT_DATE" master)`
10. Stop depot_tools from auto-updating: `export DEPOT_TOOLS_UPDATE=0`
11. Cleanup any unneeded files from the chromium source: `cd ~/chromium/src && git clean -ffd`
12. Install chromium build dependencies: `(cd build && ./install-build-deps.sh)`
13. Run hooks: `gclient sync -D --force --reset && gclient runhooks`
14. Unzip the jsgraph_release.zip file from this repo: `(cd ~/JSGraph && unzip jsgraph_release.zip)`
15. Remove unneeded function calls leftover from the WebCapsule project that can cause compilation errors:
    1. Delete or comment out the line that says `InitPlatformInstrumentation()` in third_party/WebKit/Source/web/WebKit.cpp
    2. Delete or comment out the lines that say `StartPlatformInstRecording()` and `StopPlatformInst()` in third_party/WebKit/Source/core/inspector/InspectorForensicsAgent.cpp
16. Add `'inspector/forensics/ForensicPageEvent.h'` and `'inspector/forensics/ForensicPageEvent.cpp'` to the `webcore_non_rendering_files` array in src/third_party/WebKit/Source/core/core.gypi in order to enable linking of these files
17. Copy the (updated) patched files over to replace the relevant chromium source files: `rsync -a ~/JSgraph/jsgraph_release/src/ ~/chromium/src/`
18. Generate build configs: `gn gen out/jsgraph`
19. Disable nacl for the build: Add ‘enable_nacl = false’ in the editor opened by: `gn args out/jsgraph`
20. Build the modified chromium: `ninja -C out/jsgraph chrome`
21. Setup the suid sandbox for chromium: https://chromium.googlesource.com/chromium/src.git/+/master/docs/linux/suid_sandbox_development.md


## Run instructions:
1. Make sure you're using python version 2.7. A conda virtual environment is a great way to setup a python virtual environment dedicated for this project: https://docs.anaconda.com/anaconda/install/
2. Install the JSgraph_tools dependencies: `pip install websocket-client`
3. Open a new terminal or tab and start chromium with a debugging port specified: `~/chromium/out/jsgraph/chrome --remote-debugging-port=54321`
4. In your original terminal or tab, run the devtools_client python script: `cd ~/JSgraph/JSgraph_tools && python devtools_client.py http://localhost:54321/json`
5. In the devtools_client tab, type the following commands to get started:
    1. Load a website (e.g., wikipedia.org)
    2. Choose the tab you want to record (e.g., type 0)
    3. Start recording by typing r
    4. Do some browsing (e.g., navigate through different pages on wikipedia.org)
    5. When you are ready to stop recording, type sr
6. You can view the generated logs in ~/jscapsule_logs


## Generating graphs from the logs
1. Locate the audit log for the browsing session at ~/jscapsule_logs (e.g. ~/jscapsule_logs/5_11_2017__22_40_58_0x1aa01ea29800/log.txt)
2. Use the script DrawGraphFromLog.py to generate a graph dot file from the desired audit log: `python DrawGraphFromLog.py LOG_FILE SHORTEN_URLS > OUTPUT_DOT_FILE`
    
    _LOG_FILE_: audit log file, e.g. ~/jscapsule_logs/5_11_2017__22_40_58_0x1aa01ea29800/log.txt
    
    _SHORTEN_URLS_: Shorten long URLs for better visualization or not. 1: shorten, 0: not shorten.
    
    _OUTPUT_DOT_FILE_: the name of output .dot file for the whole audit log.

3. Use script FilterSubGraph.py to do backward/forward tracking: `python FilterSubGraph.py OUTPUT_DOT_FILE NODE_ID_LIST DIRECTION HIGHLIGHT_NODE_ID_LIST> TRACKING_DOT_FILE`

    _OUTPUT_DOT_FILE_: the name of output .dot file for the whole audit log.

    _NODE_ID_LIST_: one/a list of suspected Node_id/Node_ids from OUTPUT_DOT_FILE that you want to be the pivot points, separated by comma. e.g. Node_31,Node_33

    _DIRECTION_: A: backward tracking; D: forward tracking; B: both direction.

    _HIGHLIGHT_NODE_ID_LIST_: one/a list of Node_id/Node_ids from OUTPUT_DOT_FILE that you want to be highlighted.
    
    _TRACKING_DOT_FILE_: the name of the output .dot file for only the tracked portions of the audit log.

4. Once you have the .dot files, you can use Graphviz to generate a visualization: `dot -v -T svg DOT_FILE -o OUTPUT_SVG_FILE`. 
    - If you are using Ubuntu or Debian, you can download graphviz using the command `sudo apt-get install graphviz`.


