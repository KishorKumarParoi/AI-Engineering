import { useState, useEffect } from 'react'
import Header from './components/Header'
import MorningBriefing from './components/MorningBriefing'
import TaskManager from './components/TaskManager'
import StandupGenerator from './components/StandupGenerator'
import DailyInsights from './components/DailyInsights'

const API = 'http://localhost:8000'

export default function App() {
  const [tasks, setTasks] = useState([])
  const [briefingKey, setBriefingKey] = useState(0)

  useEffect(() => {
    fetch(`${API}/tasks`)
      .then(r => r.json())
      .then(setTasks)
      .catch(console.error)
  }, [])

  return (
    <div className="min-h-screen bg-[#F8FAFC]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8">

        <Header onRefreshBriefing={() => setBriefingKey(k => k + 1)} />

        {/* Morning Briefing */}
        <div className="mt-6 fade-slide-up" style={{ animationDelay: '0.08s' }}>
          <MorningBriefing key={briefingKey} />
        </div>

        {/* Main two-column layout */}
        <div
          className="mt-6 flex flex-col lg:flex-row gap-5 fade-slide-up"
          style={{ animationDelay: '0.16s' }}
        >
          {/* Task Manager — 60% */}
          <div className="lg:w-[60%]">
            <TaskManager tasks={tasks} setTasks={setTasks} />
          </div>

          {/* Right panel — 40% */}
          <div className="lg:w-[40%] flex flex-col gap-5 lg:self-stretch">
            <StandupGenerator tasks={tasks} />
            <DailyInsights tasks={tasks} />
          </div>
        </div>
      </div>
    </div>
  )
}
