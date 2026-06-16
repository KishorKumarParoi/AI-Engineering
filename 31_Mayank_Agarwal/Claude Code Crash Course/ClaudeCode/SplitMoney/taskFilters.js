/**
 * Filter tasks based on criteria
 * @param {Array<Object>} tasks - Array of task objects
 * @param {Object} criteria - Filter criteria (status, priority, search, etc.)
 * @returns {Array<Object>} Filtered array of tasks
 */
function filterTasks(tasks, criteria = {}) {
  return tasks.filter(task => {
    if (criteria.status && task.status !== criteria.status) {
      return false;
    }

    if (criteria.priority && task.priority !== criteria.priority) {
      return false;
    }

    if (criteria.search) {
      const searchTerm = criteria.search.toLowerCase();
      const matchesSearch =
        task.title?.toLowerCase().includes(searchTerm) ||
        task.description?.toLowerCase().includes(searchTerm);
      if (!matchesSearch) {
        return false;
      }
    }

    if (criteria.startDate && task.dueDate < criteria.startDate) {
      return false;
    }

    if (criteria.endDate && task.dueDate > criteria.endDate) {
      return false;
    }

    return true;
  });
}
