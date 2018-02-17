##
# Copyright (C) 2018 University of Georgia. All rights reserved.
#
# This file is subject to the terms and conditions defined at
# https://github.com/perdisci/JSgraph/blob/master/LICENSE.txt
#
##

import sys

node_counter = 0
is_short = False

# shape_map ={ "page": "box", "":}


def read_file(filename):
    f = open(filename, "r")
    lines = f.readlines()
    f.close()
    return lines[1:]


def print_node(label, stack=None, shape=None, parent=None, edge_label=None,
               edge_style=None):
    global node_counter, is_short
    truncate_length = 80
    if shape == "house":
        truncate_length = 60
        edge_label = "EXECUTE"
    if is_short:
        label_list = label.split('\n')
        for i in range(len(label_list)):
            if len(label_list[i]) > truncate_length:
                label_list[i] = label_list[i][:truncate_length-2]+'...'
            if (label_list[i].lower().startswith("http")
                    or label_list[i].lower().startswith("url")):
                label_list[i] = label_list[i].replace("http", "hxxp", 1)
        label = '\n'.join(label_list)

    node_id = "Node_"+str(node_counter)
    str1 = node_id+' [label="'+label+'\nLogic Order: '+str(node_counter)+'"'
    if shape is not None:
        str1 += ", shape=" + shape
    str1 += "];"
    print str1
    if stack is not None:
        parent = stack[-1]
    if parent is not None:
        print_edge(node_id, parent, edge_label, edge_style)
    node_counter += 1
    return node_id


def find_paired_end(lines, i, start_string, end_string):
    counter = 1
    j = i
    while counter > 0:
        j += 1
        line = lines[j]
        if line.startswith(start_string):
            counter += 1
        elif line.startswith(end_string):
            counter -= 1
    return j


def print_edge(node_id, parent, edge_label=None, edge_style=None):
    if edge_label is None and edge_style is None and parent != "main":
        edge_label = "PARENT-CHILD"
    edge_str = parent+" -> "+node_id
    if edge_label is not None or edge_style is not None:
        edge_str += " ["
        profile_list = []
        if edge_style is not None:
            profile_list.append("style="+edge_style)
        if edge_label is not None:
            profile_list.append('label="'+edge_label+'"')
        edge_str += ','.join(profile_list)
        edge_str += "]"
    edge_str += ";"
    print edge_str


def get_value(line, key, end_string=None):
    if end_string is None:
        return line.split(key)[-1].split(',')[0].split(';')[0].strip()
    else:
        return line.split(key)[-1].split(end_string)[0].strip()


def parse_log(lines):
    stack = []
    iframe_map = dict()
    page_frame_map = dict()
    page_set = set()
    document_write_set = set()
    script_map = dict()
    scriptid2url_map = dict()
    script_node_set = set()
    callback_source_map = dict()
    window_open_node_map = dict()
    frame2url_map = dict()
    meta_refresh_node_map = dict()
    print "digraph G {"
    print "main;"
    stack.append("main")
    # first_page = True
    i = 0
    is_recording = False
    while i < len(lines):
        script_id = ""
        line = lines[i]

        if line.startswith("InspectorForensicsAgent::startRecording"):
            is_recording = True
            i += 1
            continue
        elif line.startswith("InspectorForensicsAgent::stopRecording"):
            is_recording = False
            i += 1
            continue

        if not is_recording:
            i += 1
            continue
# ##########page load################
        if line.startswith("ForensicDataStore::recordPageLoadEvent"):
            url = get_value(line, "requestURL: ", "\n")
            frame_id = get_value(line, "frame: ")
            frame2url_map[frame_id] = url
            if url in meta_refresh_node_map:
                parent = meta_refresh_node_map[url]
                node_id = print_node(url, parent=parent, shape="box",
                                     edge_style="dashed",
                                     edge_label="META REF")
            elif url in window_open_node_map:
                parent = window_open_node_map[url]
                node_id = print_node(url, parent=parent, shape="box",
                                     edge_style="dashed", edge_label="JS NAV")
            elif stack[-1] != main:
                node_id = print_node(url, stack, "box", edge_style="dashed",
                                     edge_label="USER NAV")
            page_set.add(node_id)
            page_frame_map[frame_id] = node_id
            stack.append(node_id)
            # first_page = False
        elif line.startswith("InspectorForensicsAgent::" +
                             "receivedMainResourceRedirectForensics"):
            frame_id = get_value(line, "frame: ")
            url = get_value(line, "new_URL: ", "\n")
            # replace the orignal url if redirected to judge the inline script
            frame2url_map[frame_id] = url
            node_id = print_node(url, stack, "box", edge_label="REDIRECT",
                                 edge_style="dashed")
            page_set.add(node_id)
            page_frame_map[frame_id] = node_id
            stack.append(node_id)
        elif line.startswith("ForensicDataStore::recordChildFrame"):
            frame_id = get_value(line, "frame: ")
            url = get_value(line, "requestURL: ", ", frame: ")

            parent_node_id = None
            if stack[-1] in script_node_set:
                while not lines[i+1].startswith("InspectorForensicsAgent::" +
                                                "handleCreateChildFrame" +
                                                "LoaderEndForensics"):
                    i += 1
                i += 1
                if lines[i+1].startswith("ForensicDataStore::" +
                                         "recordInsertDOMNodeEvent:"):
                    line = lines[i+1]
                    source = get_value(line, "m_nodeSource: ")
                    if source.lower().startswith("<iframe"):
                        i += 1
                        parent_node_id = print_node("Create and Insert iframe",
                                                    stack, "house")
            elif stack[-1] in document_write_set:
                parent_node_id = stack[-1]

            if parent_node_id is not None:
                node_id = print_node("iframe_"+frame_id+'\n'+url,
                                     shape="diamond", parent=parent_node_id,
                                     edge_label="CREATE", edge_style="bold")
                for stack_index in range(len(stack)-1, -1, -1):
                    if (stack[stack_index] in page_set
                            or stack[stack_index] in iframe_map.values()):
                        print_edge(node_id, stack[stack_index])
                        break
                iframe_map[frame_id] = node_id
                frame2url_map[frame_id] = url
                i += 1
                continue

            node_id = print_node("iframe_"+frame_id+'\n'+url, stack, "diamond")
            iframe_map[frame_id] = node_id
            frame2url_map[frame_id] = url

# ##########scripts###################
        elif line.startswith("InspectorForensicsAgent::" +
                             "handleCompileScriptForensics"):
            script_id = get_value(line, "Script_id:")
            url = get_value(line, "URL: ", ", line: ")
            scriptid2url_map[script_id] = url
        elif line.startswith("InspectorForensicsAgent::" +
                             "handleRunCompiledScriptStartForensics"):
            frame_id = get_value(line, "iframe: ")
            script_id = get_value(line, "Script_id: ")
            script_label = "Script_"+script_id
            if script_id in scriptid2url_map:
                url = scriptid2url_map[script_id]
                if (frame_id in frame2url_map
                        and url == frame2url_map[frame_id]):
                    script_label += "\nInline"
                else:
                    script_label += "\n"+url
            # Add a Insert Script Node,
            # if the script was created and insert into DOM
            j = find_paired_end(lines, i,
                                "InspectorForensicsAgent::" +
                                "handleRunCompiledScriptStartForensics",
                                "InspectorForensicsAgent::" +
                                "handleRunCompiledScriptEndForensics")
            line1 = lines[j+1]
            script_insert_node_id = None
            if (line1.startswith("ForensicDataStore::" +
                                 "recordInsertDOMNodeEvent:")
                    and stack[-1] in script_node_set):
                source = get_value(line1, "m_nodeSource: ")
                if source.lower().startswith("<script"):
                    script_insert_node_id = print_node("Create and Insert" +
                                                       "Script Node",
                                                       stack,
                                                       shape="house")
            elif stack[-1] in document_write_set:
                script_insert_node_id = stack[-1]

            if frame_id in iframe_map:
                node_id = print_node(script_label, parent=iframe_map[frame_id])
            elif frame_id in page_frame_map:
                node_id = print_node(script_label,
                                     parent=page_frame_map[frame_id])
            else:
                node_id = print_node(script_label, stack)
            if script_insert_node_id is not None:
                print_edge(node_id, script_insert_node_id, edge_style="bold",
                           edge_label="CREATE")
            stack.append(node_id)
            script_map[script_id] = node_id
            script_node_set.add(node_id)
        elif line.startswith("InspectorForensicsAgent::" +
                             "handleRunCompiledScriptEndForensics"):
            # print stack
            stack.pop()
# ###########Callbacks#####################
        elif line.startswith("ForensicDataStore::recordAddEventListenerEvent"):
            listener = get_value(line, "listener: ")
            event_target = get_value(line, "eventTarget: ")
            callback_source_map[event_target+","+listener] = stack[-1]
            if not stack[-1] in script_node_set:
                line = lines[i+1]
                if line.startswith("InspectorForensicsAgent::" +
                                   "handleAddEventListenerForensics"):
                    frame = get_value(line, "frame: ")
                    if frame in iframe_map:
                        callback_source_map[event_target + "," +
                                            listener] = iframe_map[frame]
                    i += 1
            else:
                line = lines[i+1]
                if line.startswith("InspectorForensicsAgent::" +
                                   "willSendXMLHttpRequest"):
                    url = get_value(line, "URL: ", "\n")
                    node_id = print_node("XMLHTTP request\nURL: "+url, stack,
                                         "house")
                    callback_source_map[event_target+","+listener] = node_id
                    i += 1
        elif line.startswith("ForensicDataStore::" +
                             "recordFireEventListenerEvent"):
            listener = get_value(line, "Event Listener: ")
            event_target = get_value(line, "EventTarget: ")
            event_interface = get_value(line, "Event interface name: ")
            event_type = get_value(line, "Event type: ")

            line = lines[i+1]
            addition_info = ""
            script_id = ""

            if line.startswith("ForensicDataStore::" +
                               "recordFireEventListenerEvent"):
                if event_interface in ["MouseEvent", "PointerEvent",
                                       "GestureEvent"]:
                    addition_info = ("Position: ("+get_value(line, "clientX: ")
                                     + ","+get_value(line, "clientY: ")+")")
                elif event_interface == "KeyboardEvent":
                    addition_info = "KeyCode: "+get_value(line, "keyCode: ")
                i += 1
                line = lines[i+1]
            if line.startswith("InspectorForensicsAgent::" +
                               "handleCallFunctionStartForensics"):
                script_id = get_value(line, "function_id:")
                function_name = get_value(line, "Name:")
                function_line = get_value(line, "line:")
                function_column = get_value(line, "column:")
                i += 1

            if script_id:
                parent = ""
                if script_id in script_map:
                    parent = script_map[script_id]
                else:
                    # To be verified: if a script_id is not registered,
                    # it should be a inline defined script on DOM 0
                    parent = callback_source_map[event_target+","+listener]
                node_id = print_node("Event_Callback:\n"+event_type+"\n" +
                                     addition_info, shape="doublecircle",
                                     parent=parent, edge_label="DEFINITION\n" +
                                     function_name+"\n("+function_line+"," +
                                     function_column+")")
                print_edge(node_id,
                           callback_source_map[event_target+","+listener],
                           edge_style="dotted", edge_label="REGISTER")
                script_node_set.add(node_id)
                stack.append(node_id)

        elif line.startswith("ForensicDataStore::recordInstallDOMTimerEvent"):
            content = get_value(line, "ExecutionContext: ")
            action = get_value(line, "ScheduledAction: ")
            callback_source_map[content+","+action] = stack[-1]
        elif line.startswith("ForensicDataStore::recordFireDOMTimerEvent"):
            action = get_value(line, "ScheduledAction: ")
            content = get_value(line, "ExecutionContext: ")
            line = lines[i+1]
            script_id = ""

            if line.startswith("InspectorForensicsAgent::" +
                               "handleCallFunctionStartForensics"):
                script_id = get_value(line, "function_id:")
                function_name = get_value(line, "Name:")
                function_line = get_value(line, "line:")
                function_column = get_value(line, "column:")
                i += 1

            if script_id:
                parent = ""
                if script_id in script_map:
                    parent = script_map[script_id]
                else:
                    # To be verified: if a script_id is not registered,
                    # it should be a inline defined script on DOM 0
                    parent = callback_source_map[content+","+action]
                node_id = print_node("Scheduled_Callback",
                                     shape="doublecircle", parent=parent,
                                     edge_label="DEFINITION\n"+function_name +
                                                "\n("+function_line+"," +
                                                function_column+")")
                print_edge(node_id, callback_source_map[content+","+action],
                           edge_style="dotted", edge_label="REGISTER")
                script_node_set.add(node_id)
                stack.append(node_id)
        elif line.startswith("InspectorForensicsAgent::" +
                             "handleRecordRegisterMutationObserverForensics"):
            observer = get_value(line, "Observer: ")
            callback_source_map[observer] = stack[-1]
        elif line.startswith("InspectorForensicsAgent::" +
                             "willDeliverMutationRecords"):
            observer = get_value(line, "Observer: ")

            line = lines[i+1]
            script_id = ""

            if line.startswith("InspectorForensicsAgent::" +
                               "handleCallFunctionStartForensics"):
                script_id = get_value(line, "function_id:")
                function_name = get_value(line, "Name:")
                function_line = get_value(line, "line:")
                function_column = get_value(line, "column:")
                i += 1

            if script_id:
                parent = ""
                if script_id in script_map:
                    parent = script_map[script_id]
                else:
                    # To be verified: if a script_id is not registered,
                    # it should be a inline defined script on DOM 0
                    parent = callback_source_map[observer]
                node_id = print_node("Mutation_Observer_Callback",
                                     shape="doublecircle", parent=parent,
                                     edge_label="DEFINITION\n"+function_name +
                                                "\n("+function_line+"," +
                                                function_column+")")
                print_edge(node_id, callback_source_map[observer],
                           edge_style="dotted", edge_label="REGISTER")
                script_node_set.add(node_id)
                stack.append(node_id)
        elif line.startswith("ForensicDataStore::" +
                             "recordRegisterFrameRequestCallbackEvent"):
            callback = get_value(line, "callback: ")
            id = get_value(line, "id: ")
            callback_source_map[id+","+callback] = stack[-1]
        elif line.startswith("ForensicDataStore::" +
                             "recordExecuteFrameRequestCallbackEvent"):
            callback = get_value(line, "callback: ")
            id = get_value(line, "id: ")
            line = lines[i+1]
            script_id = ""

            if line.startswith("InspectorForensicsAgent::" +
                               "handleCallFunctionStartForensics"):
                script_id = get_value(line, "function_id:")
                function_name = get_value(line, "Name:")
                function_line = get_value(line, "line:")
                function_column = get_value(line, "column:")
                i += 1

            if script_id:
                parent = ""
                if script_id in script_map:
                    parent = script_map[script_id]
                else:
                    # To be verified: if a script_id is not registered,
                    # it should be a inline defined script on DOM 0
                    parent = callback_source_map[id+","+callback]
                node_id = print_node("Animation_Callback",
                                     shape="doublecircle",
                                     parent=parent,
                                     edge_label="DEFINITION\n" +
                                                function_name+"\n(" +
                                                function_line+"," +
                                                function_column+")")
                print_edge(node_id, callback_source_map[id+","+callback],
                           edge_style="dotted", edge_label="REGISTER")
                script_node_set.add(node_id)
                stack.append(node_id)
        elif line.startswith("InspectorForensicsAgent::" +
                             "handleCallFunctionStartForensics"):
            script_id = get_value(line, "function_id:")
            function_name = get_value(line, "Name:")
            function_line = get_value(line, "line:")
            function_column = get_value(line, "column:")
            if script_id in script_map:
                parent = script_map[script_id]
                node_id = print_node("Callback", shape="doublecircle",
                                     parent=parent,
                                     edge_label="DEFINITION\n"+function_name +
                                                "\n("+function_line+"," +
                                                function_column+")")
            else:
                node_id = print_node("Callback", shape="doublecircle",
                                     stack=stack,
                                     edge_label=""+function_name +
                                                "\n("+function_line+"," +
                                                function_column+")")
            script_node_set.add(node_id)
            stack.append(node_id)
        elif line.startswith("InspectorForensicsAgent::" +
                             "handleCallFunctionEndForensics"):
            # print stack
            stack.pop()
# ###################critical events##################
        elif line.startswith("InspectorForensicsAgent::" +
                             "handleModaldialogConfirmResultRecording"):
            message = get_value(line, "Message: ")
            result = get_value(line, "Result: ")
            print_node("Confirm\nMessage: "+message+"\nResult: "+result,
                       stack, "house")
        elif line.startswith("InspectorForensicsAgent::" +
                             "handleModaldialogPromptResultRecording"):
            message = get_value(line, "Message: ")
            result = get_value(line, "Result: ")
            print_node("Prompt\nMessage: "+message+"\nResult: " +
                       result, stack, "house")
        elif line.startswith("InspectorForensicsAgent::" +
                             "handleModaldialogAlertRecording"):
            message = get_value(line, "Message: ")
            print_node("Alert\nMessage: "+message, stack, "house")
        elif line.startswith("InspectorForensicsAgent::" +
                             "handleDocumentWriteStart"):
            node_id = print_node("Document.write", stack, "house")
            document_write_set.add(node_id)
            stack.append(node_id)
        elif line.startswith("InspectorForensicsAgent::" +
                             "handleDocumentWriteEnd"):
            # print stack
            stack.pop()
        elif line.startswith("RenderFrameImpl::loadURLExternally"):
            url = get_value(line, "url: ", ", suggested_name: ")
            print_node("Download_Event\nURL: "+url, stack, "house")
        elif line.startswith("WebstoreBindings::Install"):
            store_url = get_value(line, "preferred_store_link_url:",
                                  ", webstore_item_id:")
            print_node("Extension Install\nURL: "+store_url, stack, "house")
        elif line.startswith("InspectorForensicsAgent::" +
                             "handleWindowOpenForensics"):
            url = get_value(line, "URL: ", ", frameName: ")
            # frameName = get_value(line, "frameName: ")
            # windowFeaturesString = get_value(line, "windowFeaturesString: ")
            # node_id = print_node("window.open:\nURL: "+url+"\nframeName: " +
            #                      frameName+"\nwindowFeaturesString: " +
            #                      windowFeaturesString,stack, "house")
            node_id = print_node("window.open:\nURL: "+url, stack, "house")
            window_open_node_map[url] = node_id
        elif line.startswith("InspectorForensicsAgent::" +
                             "handleRecordSetLocationForensics"):
            url = get_value(line, "URL: ", "\n")
            node_id = print_node("Set Location\nURL: "+url, stack, "house")
            window_open_node_map[url] = node_id
        elif line.startswith("ForensicDataStore::recordCookieDataStore"):
            cookie = line.split("cookieString: ")[-1].strip()
            print_node("Get Cookie:\n"+cookie, stack, "house")
        elif line.startswith("InspectorForensicsAgent::didModifyDOMAttr"):
            source = get_value(line, "m_nodeSource: ")
            if stack[-1] in script_node_set and source.startswith("<img "):
                if len(source.split("src=")) < 2:
                    i += 1
                    continue
                src = source.split("src=")[1]
                src = src.split('"')[1]
                # src = src.split("'")[0]
                print_node("Load Image:\n"+src, stack, "house")
        elif line.startswith("InspectorForensicsAgent::" +
                             "handleWindowFocusForensics"):
            frame = get_value(line, "frame: ")
            node_id = print_node("window.focous:\nframe: "+frame, stack,
                                 "house")
        elif line.startswith("LocalDOMWindow::blur"):
            frame = line.split(":")[-1]
            node_id = print_node("window.blur\nframe:"+frame, stack, "house")
        elif line.startswith("InspectorForensicsAgent::" +
                             "handleRequestFullscreenForensics"):
            element = get_value(line, "Element: ")
            node_id = print_node("elememt.requestFullscreen\nelement:"+element,
                                 stack, "house")
        elif line.startswith("InspectorForensicsAgent::" +
                             "handleExitFullscreenForensics"):
            node_id = print_node("document.exitFullscreen", stack, "house")
        elif line.startswith("InspectorForensicsAgent::" +
                             "handleMaybeHandleHttpRefreshForensics"):
            frame_id = get_value(line, "Frame: ")
            url = get_value(line, "URL: ", ", Delay:")
            delay = get_value(line, "Delay: ")
            label = "Meta Refresh:\nURL: "+url+"\ndelay:"+delay
            if frame_id in iframe_map:
                node_id = print_node(label, parent=iframe_map[frame_id],
                                     shape="house")
            elif frame_id in page_frame_map:
                node_id = print_node(label, parent=page_frame_map[frame_id],
                                     shape="house")
            else:
                node_id = print_node(label, stack, shape="house")
            meta_refresh_node_map[url] = node_id

        i += 1

    print "}"


def main():
    global is_short
    if len(sys.argv) >= 3 and sys.argv[2] == '1':
        is_short = True
    parse_log(read_file(sys.argv[1]))


if __name__ == '__main__':
    main()
