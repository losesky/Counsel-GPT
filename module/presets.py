# -*- coding:utf-8 -*-
import gradio as gr

webui_title = """
# Counsel-AI
"""

init_message = (f"""欢迎使用 <b>Counsel-AI</b>！你可以轻松地向人工智能律师咨询法律问题，并获得准确的法律建议和指导。也可以根据需要，切换模式获得不同信息。""")

knowledge_answer = (f"""你已进入【专业问答】模式，选择知识库名称后，即可开始问答。您输入的任何问题都将基于现有知识库做出回答，如有需要在【知识库配置】栏上传资料丰富知识库内容。""")

kowledge_retrieval = (f"""你已进入【知识库检索】模式，将根据你输入的内容进行知识库检索。检索结果仅输出知识库匹配的内容，知识相关度 Score 分值越低越匹配。""")

bing_answer = (f"""你已进入【在线问答】模式，你输入的任何问题都将进行在线搜索，会根据外部信息给到你最好的建议和指导。""")


small_and_beautiful_theme = gr.themes.Soft(
        primary_hue=gr.themes.Color(
            c50="#EBFAF2",
            c100="#CFF3E1",
            c200="#A8EAC8",
            c300="#77DEA9",
            c400="#3FD086",
            c500="#02C160",
            c600="#06AE56",
            c700="#05974E",
            c800="#057F45",
            c900="#04673D",
            c950="#2E5541",
            name="small_and_beautiful",
        ),
        secondary_hue=gr.themes.Color(
            c50="#576b95",
            c100="#576b95",
            c200="#576b95",
            c300="#576b95",
            c400="#576b95",
            c500="#576b95",
            c600="#576b95",
            c700="#576b95",
            c800="#576b95",
            c900="#576b95",
            c950="#576b95",
        ),
        neutral_hue=gr.themes.Color(
            name="gray",
            c50="#f6f7f8",
            # c100="#f3f4f6",
            c100="#F2F2F2",
            c200="#e5e7eb",
            c300="#d1d5db",
            c400="#B2B2B2",
            c500="#808080",
            c600="#636363",
            c700="#515151",
            c800="#393939",
            # c900="#272727",
            c900="#2B2B2B",
            c950="#171717",
        ),
        radius_size=gr.themes.sizes.radius_sm,
    ).set(
        # button_primary_background_fill="*primary_500",
        button_primary_background_fill_dark="*primary_600",
        # button_primary_background_fill_hover="*primary_400",
        # button_primary_border_color="*primary_500",
        button_primary_border_color_dark="*primary_600",
        button_primary_text_color="wihte",
        button_primary_text_color_dark="white",
        button_secondary_background_fill="*neutral_100",
        button_secondary_background_fill_hover="*neutral_50",
        button_secondary_background_fill_dark="*neutral_900",
        button_secondary_text_color="*neutral_800",
        button_secondary_text_color_dark="white",
        # background_fill_primary="#F7F7F7",
        # background_fill_primary_dark="#1F1F1F",
        # block_title_text_color="*primary_500",
        block_title_background_fill_dark="*primary_900",
        block_label_background_fill_dark="*primary_900",
        input_background_fill="#F6F6F6",
        chatbot_code_background_color="*neutral_950",
        chatbot_code_background_color_dark="*neutral_950",
    )
