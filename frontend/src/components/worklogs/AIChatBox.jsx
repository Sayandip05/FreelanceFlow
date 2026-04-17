import { useState, useRef, useEffect } from 'react'
import { aiChatAPI, uploadAPI, deliverableAPI } from '../../api/worklogs'
import { PaperAirplaneIcon, PaperClipIcon, XMarkIcon, CheckCircleIcon } from '@heroicons/react/24/outline'

const AIChatBox = ({ contractId, projectName, onDeliverableCreated }) => {
  const [messages, setMessages] = useState([
    {
      role: 'assistant',
      content: `Hello! I'm your AI worklog assistant for "${projectName}". Tell me what you've been working on, and I'll help you create a professional deliverable report. You can also upload screenshots or files as proof of your work.`,
    },
  ])
  const [inputMessage, setInputMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [isUploading, setIsUploading] = useState(false)
  const [reportReady, setReportReady] = useState(false)
  const [reportData, setReportData] = useState(null)
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputMessage.trim() || isLoading) return

    const userMessage = inputMessage.trim()
    setInputMessage('')
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])
    setIsLoading(true)

    try {
      const chatHistory = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }))

      const response = await aiChatAPI.sendMessage(contractId, userMessage, chatHistory)
      
      const aiMessage = {
        role: 'assistant',
        content: response.data.message,
      }
      
      setMessages((prev) => [...prev, aiMessage])
      
      if (response.data.report_ready && response.data.report_data) {
        setReportReady(true)
        setReportData(response.data.report_data)
      }
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Sorry, I encountered an error. Please try again.',
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    setIsUploading(true)
    try {
      const response = await uploadAPI.uploadFile(file)
      const fileUrl = response.data.url
      
      setUploadedFiles((prev) => [...prev, { name: file.name, url: fileUrl }])
      setMessages((prev) => [
        ...prev,
        {
          role: 'user',
          content: `[Uploaded file: ${file.name}]`,
          isFile: true,
        },
      ])
    } catch (error) {
      alert('Failed to upload file. Please try again.')
    } finally {
      setIsUploading(false)
    }
  }

  const removeFile = (index) => {
    setUploadedFiles((prev) => prev.filter((_, i) => i !== index))
  }

  const generateDeliverable = async () => {
    if (!reportReady) return

    setIsLoading(true)
    try {
      const chatTranscript = messages.map((m) => ({
        role: m.role,
        content: m.content,
      }))

      const fileUrls = uploadedFiles.map((f) => f.url)
      
      const response = await aiChatAPI.generateDeliverable(
        contractId,
        chatTranscript,
        fileUrls
      )

      onDeliverableCreated?.(response.data)
      
      // Reset chat
      setMessages([
        {
          role: 'assistant',
          content: `Great! I've created your deliverable. You can now review it and submit it for client approval.`,
        },
      ])
      setUploadedFiles([])
      setReportReady(false)
      setReportData(null)
    } catch (error) {
      alert('Failed to create deliverable. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className="flex flex-col h-[600px] bg-white rounded-lg shadow-lg border border-gray-200">
      {/* Header */}
      <div className="px-4 py-3 border-b border-gray-200 bg-gradient-to-r from-indigo-600 to-purple-600 rounded-t-lg">
        <h3 className="text-white font-semibold flex items-center gap-2">
          <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
          AI Worklog Assistant
        </h3>
        <p className="text-indigo-100 text-sm">{projectName}</p>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${
              message.role === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[80%] rounded-lg px-4 py-2 ${
                message.role === 'user'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-800'
              } ${message.isFile ? 'italic opacity-75' : ''}`}
            >
              <p className="whitespace-pre-wrap text-sm">{message.content}</p>
            </div>
          </div>
        ))}
        
        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-100 rounded-lg px-4 py-2 flex items-center gap-2">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-100"></span>
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce delay-200"></span>
              </div>
              <span className="text-sm text-gray-500">AI is typing...</span>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>

      {/* Report Ready Banner */}
      {reportReady && (
        <div className="mx-4 mb-2 p-3 bg-green-50 border border-green-200 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircleIcon className="w-5 h-5 text-green-600" />
            <span className="text-green-800 font-medium text-sm">
              Report Ready!
            </span>
          </div>
          {reportData && (
            <div className="text-sm text-green-700 mb-3">
              <p><strong>Title:</strong> {reportData.title}</p>
              <p><strong>Hours:</strong> {reportData.hours_worked}h</p>
            </div>
          )}
          <button
            onClick={generateDeliverable}
            disabled={isLoading}
            className="w-full bg-green-600 text-white py-2 rounded-lg hover:bg-green-700 transition-colors text-sm font-medium disabled:opacity-50"
          >
            {isLoading ? 'Creating...' : 'Create Deliverable'}
          </button>
        </div>
      )}

      {/* Uploaded Files */}
      {uploadedFiles.length > 0 && (
        <div className="px-4 py-2 border-t border-gray-100">
          <p className="text-xs text-gray-500 mb-2">Attached files:</p>
          <div className="flex flex-wrap gap-2">
            {uploadedFiles.map((file, index) => (
              <div
                key={index}
                className="flex items-center gap-1 bg-gray-100 px-2 py-1 rounded text-xs"
              >
                <span className="truncate max-w-[150px]">{file.name}</span>
                <button
                  onClick={() => removeFile(index)}
                  className="text-gray-500 hover:text-red-500"
                >
                  <XMarkIcon className="w-3 h-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="p-4 border-t border-gray-200">
        <div className="flex items-end gap-2">
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="p-2 text-gray-500 hover:text-indigo-600 transition-colors rounded-lg hover:bg-gray-100"
          >
            <PaperClipIcon className="w-5 h-5" />
          </button>
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileUpload}
            className="hidden"
            accept="image/*,.pdf"
          />
          
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Describe what you've worked on..."
            className="flex-1 resize-none border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500 max-h-32"
            rows={2}
            disabled={isLoading}
          />
          
          <button
            onClick={handleSendMessage}
            disabled={!inputMessage.trim() || isLoading}
            className="p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <PaperAirplaneIcon className="w-5 h-5" />
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2">
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}

export default AIChatBox
