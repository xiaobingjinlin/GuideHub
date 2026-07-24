import GradioEmbed from './GradioEmbed'

/** LangGraph · 文本对话机器人（Gradio + SqliteSaver checkpoint） */
export default function LangGraphTextChatBot(props) {
  return (
    <GradioEmbed
      {...props}
      eyebrow="LangGraph · Gradio"
      gradioPath="/gradio/langgraph-text-chat/"
    />
  )
}
