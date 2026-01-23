import React, { useState } from 'react';
import { Calendar, User, AlertTriangle, GripVertical } from 'lucide-react';

const COLUMNS = [
  { id: 'todo', title: 'To Do', color: 'bg-slate-100 border-slate-300' },
  { id: 'in_progress', title: 'In Progress', color: 'bg-blue-50 border-blue-300' },
  { id: 'completed', title: 'Completed', color: 'bg-green-50 border-green-300' },
  { id: 'cancelled', title: 'Cancelled', color: 'bg-red-50 border-red-300' }
];

const KanbanBoard = ({ tasks, onStatusChange, onTaskClick }) => {
  const [draggedTask, setDraggedTask] = useState(null);
  const [dragOverColumn, setDragOverColumn] = useState(null);

  const getTasksByStatus = (status) => {
    return tasks.filter(task => task.status === status);
  };

  const handleDragStart = (e, task) => {
    setDraggedTask(task);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/plain', task.id);
  };

  const handleDragEnd = () => {
    setDraggedTask(null);
    setDragOverColumn(null);
  };

  const handleDragOver = (e, columnId) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverColumn(columnId);
  };

  const handleDragLeave = () => {
    setDragOverColumn(null);
  };

  const handleDrop = (e, newStatus) => {
    e.preventDefault();
    if (draggedTask && draggedTask.status !== newStatus) {
      onStatusChange(draggedTask.id, newStatus);
    }
    setDraggedTask(null);
    setDragOverColumn(null);
  };

  const getPriorityColor = (priority) => {
    const colors = {
      high: 'bg-red-500',
      medium: 'bg-yellow-500',
      low: 'bg-green-500'
    };
    return colors[priority] || colors.medium;
  };

  const isOverdue = (task) => {
    if (task.status === 'completed' || task.status === 'cancelled') return false;
    return new Date(task.due_date) < new Date();
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
  };

  return (
    <div className="flex gap-4 overflow-x-auto pb-4" data-testid="kanban-board">
      {COLUMNS.map(column => (
        <div
          key={column.id}
          className={`flex-1 min-w-[280px] max-w-[350px] rounded-lg border-2 ${column.color} ${
            dragOverColumn === column.id ? 'ring-2 ring-primary ring-offset-2' : ''
          }`}
          onDragOver={(e) => handleDragOver(e, column.id)}
          onDragLeave={handleDragLeave}
          onDrop={(e) => handleDrop(e, column.id)}
          data-testid={`kanban-column-${column.id}`}
        >
          {/* Column Header */}
          <div className="p-3 border-b border-inherit">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold text-text-primary">{column.title}</h3>
              <span className="bg-white px-2 py-0.5 rounded-full text-sm font-medium text-text-secondary">
                {getTasksByStatus(column.id).length}
              </span>
            </div>
          </div>

          {/* Task Cards */}
          <div className="p-2 space-y-2 min-h-[200px] max-h-[calc(100vh-350px)] overflow-y-auto">
            {getTasksByStatus(column.id).map(task => (
              <div
                key={task.id}
                draggable
                onDragStart={(e) => handleDragStart(e, task)}
                onDragEnd={handleDragEnd}
                onClick={() => onTaskClick(task.id)}
                className={`bg-white rounded-lg border shadow-sm p-3 cursor-grab active:cursor-grabbing hover:shadow-md transition-all ${
                  draggedTask?.id === task.id ? 'opacity-50 scale-95' : ''
                } ${isOverdue(task) ? 'border-red-300 bg-red-50/50' : 'border-slate-200'}`}
                data-testid={`kanban-task-${task.id}`}
              >
                {/* Priority Indicator & Grip */}
                <div className="flex items-center gap-2 mb-2">
                  <GripVertical size={14} className="text-slate-400 flex-shrink-0" />
                  <div className={`w-2 h-2 rounded-full ${getPriorityColor(task.priority)}`} />
                  <span className="text-xs text-text-secondary capitalize">{task.priority}</span>
                  {isOverdue(task) && (
                    <AlertTriangle size={14} className="text-red-500 ml-auto" />
                  )}
                </div>

                {/* Title */}
                <h4 className="font-medium text-text-primary text-sm line-clamp-2 mb-2">
                  {task.title}
                </h4>

                {/* Meta Info */}
                <div className="flex items-center justify-between text-xs text-text-secondary">
                  <div className="flex items-center gap-1 truncate max-w-[60%]">
                    <User size={12} />
                    <span className="truncate">{task.assigned_to_name?.split(' ')[0]}</span>
                  </div>
                  <div className={`flex items-center gap-1 ${isOverdue(task) ? 'text-red-600 font-medium' : ''}`}>
                    <Calendar size={12} />
                    <span>{formatDate(task.due_date)}</span>
                  </div>
                </div>
              </div>
            ))}

            {/* Empty State */}
            {getTasksByStatus(column.id).length === 0 && (
              <div className="flex items-center justify-center h-24 text-text-secondary text-sm">
                No tasks
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  );
};

export default KanbanBoard;
