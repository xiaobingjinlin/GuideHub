import GradioEmbed from './GradioEmbed'

/** LangChain · 文本对话机器人（Gradio + 思考模式 + SQLite 长期记忆） */
export default function TextChatBot(props) {
  return <GradioEmbed {...props} gradioPath="/gradio/text-chat/" />
}
