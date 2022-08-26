import { getCategorizedApplicationCommands } from "./getCategorizedApplicationCommands"

export const getApplicationCommands = () => {
  return getCategorizedApplicationCommands().flatMap((commands) => commands)
}
