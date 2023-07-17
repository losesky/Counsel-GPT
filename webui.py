import gradio as gr
import os

from configs.model_config import *
import models.shared as shared
from module.overwrites import *
from module.presets import *
from module.model_func import *
from module.crawling import init_all, run_crawling

# 初始化消息
model_status = init_model()

with open("assets/custom.css", "r", encoding="utf-8") as f:
    customCSS = f.read()

gr.Chatbot._postprocess_chat_messages = postprocess_chat_messages
gr.Chatbot.postprocess = postprocess

with gr.Blocks(css=customCSS, theme=small_and_beautiful_theme) as demo:
    vs_path, file_status, model_status = gr.State(
        os.path.join(KB_ROOT_PATH, get_vs_list()[0], "vector_store") if len(get_vs_list()) > 1 else ""), gr.State(
        ""), gr.State(
        model_status)
        
    promptTemplates = gr.State(load_template(get_template_names(plain=True)[0], mode=2))
    
    with gr.Row():
        with gr.Column(min_width=219, scale=98):
            with gr.Row():
                gr.HTML(webui_title, elem_id="app_title")
                status_display = gr.Markdown(model_status.value, elem_id="status_display")
        with gr.Column(min_width=48, scale=1):
            gr.HTML(get_html("appearance_switcher.html").format(label=""))

    dialog = gr.Tab("对话")
    
    with dialog:
        with gr.Row():
            with gr.Column(scale=15):
                with gr.Row():
                    chatbot = gr.Chatbot([[None, init_message]],
                                        elem_id="chat-box",
                                        show_label=False)
                with gr.Row():
                    with gr.Column(min_width=225, scale=12):
                        query = gr.Textbox(show_label=False,
                                   container=False,
                                   max_lines=3,
                                   placeholder="请输入提问内容，按回车提交")
                    with gr.Column(min_width=42, scale=1):
                        submitBtn = gr.Button(value="", variant="primary", elem_id="submit_btn")
                        cancelBtn = gr.Button(value="", variant="secondary", visible=False, elem_id="cancel_btn")
            with gr.Column(scale=5):
                    # 问答模式
                    dialog_tab = gr.Accordion(label="模式选择", visible=True, open=False)
                    with dialog_tab:
                        mode = gr.Dropdown(["通用对话", "在线问答", "专业问答", "知识库检索"],
                                                label="请选择使用模式",
                                                interactive=True,
                                                value="通用对话")
                        select_vs_v1 = gr.Dropdown(get_vs_list(),
                                                label="请选择要加载的知识库",
                                                interactive=True,
                                                visible=False,
                                                value=get_vs_list()[0] if len(get_vs_list()) > 0 else None)
                        
                        search_source = gr.Radio(['Baidu - 百度','Google - 谷歌','Bing - 必应'],
                             label="信息来源",
                             value='Baidu - 百度',
                             visible=False,
                             elem_id='search_source',
                             interactive=True)
                        
                        search_rang = gr.Radio(['全网', '概要', '上下文'],
                             label="答题范围",
                             value='全网',
                             visible=False,
                             interactive=True)
                        
                    # 提示词模板
                    # prompt_tab = gr.Accordion(label="提示词模板",
                    #                           visible=True,
                    #                           open=False)
                    # with prompt_tab:
                        templateFileSelectDropdown = gr.Dropdown(
                                            label=("选择提示词集合文件"),
                                            visible=False,
                                            choices=get_template_names(plain=True),
                                            multiselect=False,
                                            value=get_template_names(plain=True)[0],
                                        )
                        templateSelectDropdown = gr.Dropdown(
                                            label=("选择提示词模板"),
                                            choices=load_template(
                                                get_template_names(plain=True)[0],
                                                mode=1
                                            ),
                                            value=load_template(
                                                get_template_names(plain=True)[0],
                                                mode=1
                                            )[0],
                                            multiselect=False,
                                        )
                        systemPromptTxt = gr.Textbox(
                            show_label=True,
                            placeholder=("在这里输入系统提示词..."),
                            label="系统提示词",
                            value=SYSTEM_PROMPT,
                            lines=10,
                            max_lines=10,
                        )
                        templateRefreshBtn = gr.Button(("🔄 刷新"), visible=False)
                        
                    # 隐藏参数
                    score_threshold = gr.Slider(0, 1000,
                                                    value=VECTOR_SEARCH_SCORE_THRESHOLD,
                                                    step=100,
                                                    label="分值越低内容匹配度越高",
                                                    interactive=True,
                                                    visible=False)
                    vector_search_top_k = gr.Number(value=VECTOR_SEARCH_TOP_K,
                                                    precision=0,
                                                    label="获取知识库内容条数",
                                                    interactive=True,
                                                    visible=False)
                    chunk_conent = gr.Checkbox(value=True,
                                                visible=False,
                                                label="是否启用上下文关联",
                                                interactive=True)
                    
                    chunk_sizes = gr.Number(value=CHUNK_SIZE,
                                            precision=0,
                                            label="匹配单段内容的连接上下文后最大长度",
                                            interactive=True,
                                            visible=False)

                    templateRefreshBtn.click(get_template_names, None, [templateFileSelectDropdown])
                    
                    templateFileSelectDropdown.change(
                        load_template,
                        [templateFileSelectDropdown],
                        [promptTemplates, templateSelectDropdown],
                        show_progress=True,
                    )
                    
                    templateSelectDropdown.change(
                        get_template_content,
                        [promptTemplates, templateSelectDropdown, systemPromptTxt],
                        [systemPromptTxt],
                        show_progress=True,
                    )
                    
                    chunk_conent.change(fn=change_chunk_conent,
                                        inputs=[chunk_conent, gr.Textbox(value="chunk_conent", visible=False), chatbot],
                                        outputs=[chunk_sizes, status_display])
                    systemPromptTxt.change(fn=change_prompt,
                                        inputs=[templateSelectDropdown],
                                        outputs=[chatbot])
                    mode.change(fn=change_mode,
                                inputs=[mode, chatbot, select_vs_v1],
                                outputs=[select_vs_v1, score_threshold, vector_search_top_k, templateFileSelectDropdown, templateSelectDropdown, systemPromptTxt, search_source, search_rang, chatbot])
                    
                    select_vs_v1.change(fn=select_vs_change,
                                inputs=[select_vs_v1, chatbot, mode],
                                outputs=[vs_path, score_threshold, vector_search_top_k, status_display])
                    
                    cancelBtn.click(cancel_outputing, [], []).then(end_outputing, [], [submitBtn, cancelBtn])

                    query.submit(start_outputing, [], [submitBtn, cancelBtn], show_progress=True).then(get_answer,
                                        [query, vs_path, chatbot, mode, search_source, search_rang, score_threshold, vector_search_top_k, chunk_conent, chunk_sizes, systemPromptTxt],
                                        [chatbot, query, status_display], show_progress=False).then(end_outputing, [], [submitBtn, cancelBtn], show_progress=True)

                    submitBtn.click(start_outputing, [], [submitBtn, cancelBtn], show_progress=True).then(get_answer,
                                        [query, vs_path, chatbot, mode, search_source, search_rang, score_threshold, vector_search_top_k, chunk_conent, chunk_sizes, systemPromptTxt],
                                        [chatbot, query, status_display], show_progress=False).then(end_outputing, [], [submitBtn, cancelBtn], show_progress=True)
                    
                    
                    flag_csv_logger.setup([query, vs_path, chatbot, mode], "flagged")
                
    with gr.Tab("知识库配置"):
        select_vs_v2 = gr.Dropdown(get_vs_list(),
                                label="请选择要加载的知识库",
                                interactive=True,
                                value=get_vs_list()[0] if len(get_vs_list()) > 0 else None)
        vs_name = gr.Textbox(label="请输入新建知识库名称",
                                lines=1,
                                interactive=True,
                                visible=True)
        vs_add = gr.Button(value="添加至知识库", visible=True)
        vs_refresh = gr.Button("更新本知识库", visible=False)
        vs_delete = gr.Button("删除本知识库", visible=False)
        # load_knowlege_button = gr.Button("重新构建知识库", visible=False)  # 待处理
        file2vs = gr.Column(visible=False)
        with file2vs:
            gr.Markdown("向知识库中添加单条内容或文件", visible=False)
            sentence_size = gr.Number(value=SENTENCE_SIZE,
                                      precision=0,
                                      label="文本入库分句长度限制",
                                      interactive=True,
                                      visible=False)
            with gr.Tab("从网站抓取"):
                with gr.Row():
                    with gr.Column(scale=5):
                        spider_url = gr.Textbox(label="网址",
                                                placeholder="请输入网址",
                                                interactive=False,
                                                value=SPIDER_URL,
                                                lines=1)
                    with gr.Column(scale=5):
                        keywords = gr.Textbox(label="关键词",
                                            placeholder="请输入关键词",
                                            value='',
                                            lines=1)
                logs_chat = gr.Chatbot([[None, None]],
                                    elem_id="logs_chat",
                                    label='日志')
                spider_btn = gr.Button("开始抓取内容", visible=True)
                clear_btn = gr.ClearButton([keywords, logs_chat], visible=False)

                
                
            with gr.Tab("上传文件"):
                files = gr.File(label="添加文件",
                                file_types=['.txt', '.md', '.docx', '.pdf'],
                                file_count="multiple",
                                show_label=False
                                )
                load_file_button = gr.Button("上传文件并加载知识库")
            with gr.Tab("上传文件夹"):
                folder_files = gr.File(label="添加文件",
                                        # file_types=['.txt', '.md', '.docx', '.pdf'],
                                        file_count="directory",
                                        show_label=False)
                load_folder_button = gr.Button("上传文件夹并加载知识库")
            with gr.Tab("添加单条内容"):
                one_title = gr.Textbox(label="标题", placeholder="请输入要添加单条段落的标题", lines=1)
                one_conent = gr.Textbox(label="内容", placeholder="请输入要添加单条段落的内容", lines=5)
                one_content_segmentation = gr.Checkbox(value=True, label="禁止内容分句入库",
                                                        interactive=True)
                load_conent_button = gr.Button("添加内容并加载知识库")
            
            with gr.Tab("删除文件"):
                files_to_delete = gr.CheckboxGroup(choices=[],
                                                label="请从知识库已有文件中选择要删除的文件",
                                                interactive=True)
                delete_file_button = gr.Button("从知识库中删除选中文件")

            vs_refresh.click(fn=refresh_vs_list,
                             inputs=[],
                             outputs=[select_vs_v1, select_vs_v2])
            vs_add.click(fn=add_vs_name,
                         inputs=[vs_name],
                         outputs=[select_vs_v2, vs_name, vs_add, file2vs, status_display, vs_delete])
            vs_delete.click(fn=delete_vs,
                            inputs=[select_vs_v2, chatbot],
                            outputs=[select_vs_v2, vs_name, vs_add, file2vs, status_display, vs_delete])
            select_vs_v2.change(fn=change_vs_name_input,
                             inputs=[select_vs_v2, chatbot],
                             outputs=[vs_name, vs_add, file2vs, vs_path, status_display, files_to_delete, vs_delete, vs_refresh])
            load_file_button.click(get_vector_store,
                                   show_progress=True,
                                   inputs=[select_vs_v2, files, sentence_size, chatbot, one_conent, one_content_segmentation],
                                   outputs=[vs_path, files, status_display, files_to_delete, select_vs_v1, select_vs_v2], )
            load_folder_button.click(get_vector_store,
                                     show_progress=True,
                                     inputs=[select_vs_v2, folder_files, sentence_size, chatbot, one_conent,
                                             one_content_segmentation],
                                     outputs=[vs_path, folder_files, status_display, files_to_delete, select_vs_v1, select_vs_v2], )
            load_conent_button.click(get_vector_store,
                                    show_progress=True,
                                    inputs=[select_vs_v2, one_title, sentence_size, chatbot,
                                            one_conent, one_content_segmentation],
                                    outputs=[vs_path, one_title, one_conent, files_to_delete, select_vs_v1, select_vs_v2], )
            delete_file_button.click(delete_file,
                                     show_progress=True,
                                     inputs=[select_vs_v2, files_to_delete, chatbot],
                                     outputs=[files_to_delete, status_display])
            # load_knowlege_button.click(reinit_vector_store, show_progress=True,
            #                        inputs=[select_vs_v2, chatbot], outputs=status_display)
            spider_btn.click(run_crawling, [spider_url, keywords, logs_chat, select_vs_v2, vs_path, sentence_size], [logs_chat, spider_btn, clear_btn, files_to_delete])
            clear_btn.click(init_all, None, [spider_btn, clear_btn])
                
    with gr.Tab("模型配置"):
        llm_model = gr.Radio(llm_model_dict_list,
                             label="LLM Models",
                             value=LLM_MODEL,
                             interactive=True)
        
        no_remote_model = gr.Checkbox(shared.LoaderCheckPoint.no_remote_model,
                                      label="加载本地模型",
                                      interactive=True)

        llm_history_len = gr.Slider(0, 10,
                                    value=LLM_HISTORY_LEN,
                                    step=1,
                                    label="通用对话轮数",
                                    interactive=True)
        
        use_ptuning_v2 = gr.Checkbox(USE_PTUNING_V2,
                                     label="使用p-tuning-v2微调过的模型",
                                     visible=False,
                                     interactive=True)
        
        use_lora = gr.Checkbox(USE_LORA,
                               label="使用lora微调的权重",
                               visible=False,
                               interactive=True)
        
        embedding_model = gr.Radio(embedding_model_dict_list,
                                   label="Embedding Models",
                                   value=EMBEDDING_MODEL,
                                   interactive=True)
        
        temperature = gr.Slider(
                            minimum=0.01,
                            maximum=0.5,
                            value=0.01,
                            step=0.01,
                            interactive=True,
                            label="Temperature"
                        )
        
        top_k = gr.Slider(1, 20, value=VECTOR_SEARCH_TOP_K, step=1,
                          label="向量匹配 top k", interactive=True)
        
        load_model_button = gr.Button("重新加载模型")
        
        load_model_button.click(reinit_model, show_progress=True,
                                inputs=[llm_model, embedding_model, llm_history_len, no_remote_model, use_ptuning_v2,
                                        use_lora, temperature, top_k, chatbot], outputs=status_display)
        
    demo.load(
        fn=refresh_vs_list,
        inputs=None,
        outputs=[select_vs_v1, select_vs_v2],
        queue=True,
        show_progress=False,
    )
            
    dialog.select(
        fn=refresh_vs_list,
        inputs=None,
        outputs=[select_vs_v1, select_vs_v2],
        queue=True,
        show_progress=False,
    )

if __name__ == "__main__":
    reload_javascript()
    demo.title = webui_title
    local_url = demo.queue(concurrency_count=100).launch(
            server_name='0.0.0.0',
            server_port=APP_PORT,
            show_api=False,
            share=False,
            inbrowser=False
            )
