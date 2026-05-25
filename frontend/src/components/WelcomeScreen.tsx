import { useState } from 'react'

interface WelcomeScreenProps {
  onCreateRoom: (name: string) => Promise<void>
  onJoinRoom: (roomId: number, name: string, secret: string) => Promise<void>
}

export default function WelcomeScreen({ onCreateRoom, onJoinRoom }: WelcomeScreenProps) {
  const [mode, setMode] = useState<'welcome' | 'create' | 'join'>('welcome')
  const [roomName, setRoomName] = useState('')
  const [joinRoomId, setJoinRoomId] = useState('')
  const [joinName, setJoinName] = useState('')
  const [joinSecret, setJoinSecret] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const handleCreate = async () => {
    if (!roomName.trim()) return
    setLoading(true)
    setError('')
    try {
      await onCreateRoom(roomName.trim())
    } catch (e: any) {
      setError(e.message || '创建失败')
    } finally {
      setLoading(false)
    }
  }

  const handleJoin = async () => {
    const id = parseInt(joinRoomId)
    if (isNaN(id)) {
      setError('房间 ID 必须是数字')
      return
    }
    if (!joinName.trim()) {
      setError('请输入你的名称')
      return
    }
    setLoading(true)
    setError('')
    try {
      await onJoinRoom(id, joinName.trim(), joinSecret.trim())
    } catch (e: any) {
      setError(e.message || '加入失败')
    } finally {
      setLoading(false)
    }
  }

  if (mode === 'welcome') {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-6">
        <div className="text-6xl mb-4">🤖</div>
        <h1 className="text-3xl font-bold mb-2 text-gray-100">欢迎来到 AgentRoom</h1>
        <p className="text-gray-400 mb-8 max-w-md">
          本地多 Agent 协作平台。让多个 AI Agent 像人类团队一样在聊天室里实时协作。
        </p>
        <div className="flex gap-4">
          <button
            onClick={() => setMode('create')}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg font-medium transition"
          >
            创建房间
          </button>
          <button
            onClick={() => setMode('join')}
            className="px-6 py-3 bg-gray-700 hover:bg-gray-600 text-white rounded-lg font-medium transition"
          >
            加入房间
          </button>
        </div>
      </div>
    )
  }

  if (mode === 'create') {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-6">
        <h2 className="text-2xl font-bold mb-4 text-gray-100">创建第一个房间</h2>
        <div className="w-full max-w-sm space-y-4">
          <input
            type="text"
            placeholder="房间名称，如: demo"
            value={roomName}
            onChange={(e) => setRoomName(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleCreate()}
            className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500"
            autoFocus
          />
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <div className="flex gap-3">
            <button
              onClick={() => setMode('welcome')}
              className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition"
            >
              返回
            </button>
            <button
              onClick={handleCreate}
              disabled={loading || !roomName.trim()}
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 text-white rounded-lg transition"
            >
              {loading ? '创建中...' : '创建'}
            </button>
          </div>
        </div>
      </div>
    )
  }

  // join mode
  return (
    <div className="flex flex-col items-center justify-center h-full text-center px-6">
      <h2 className="text-2xl font-bold mb-4 text-gray-100">加入房间</h2>
      <div className="w-full max-w-sm space-y-3">
        <input
          type="text"
          placeholder="房间 ID"
          value={joinRoomId}
          onChange={(e) => setJoinRoomId(e.target.value)}
          className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500"
          autoFocus
        />
        <input
          type="text"
          placeholder="你的名称"
          value={joinName}
          onChange={(e) => setJoinName(e.target.value)}
          className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500"
        />
        <input
          type="text"
          placeholder="房间 secret（可选）"
          value={joinSecret}
          onChange={(e) => setJoinSecret(e.target.value)}
          className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:border-blue-500"
        />
        {error && <p className="text-red-400 text-sm">{error}</p>}
        <div className="flex gap-3">
          <button
            onClick={() => setMode('welcome')}
            className="flex-1 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded-lg transition"
          >
            返回
          </button>
          <button
            onClick={handleJoin}
            disabled={loading || !joinRoomId.trim() || !joinName.trim()}
            className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-500 disabled:bg-gray-600 text-white rounded-lg transition"
          >
            {loading ? '加入中...' : '加入'}
          </button>
        </div>
      </div>
    </div>
  )
}
