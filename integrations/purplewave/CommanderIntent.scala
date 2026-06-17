package Commander

final case class CommanderStyle(
  aggression: Double = 0.5,
  harass: Double = 0.5,
  economyGreed: Double = 0.5,
  defensiveSafety: Double = 0.5,
  allInCommitment: Double = 0.2)

final case class CommanderCommand(
  id: String,
  commandType: String,
  action: String,
  payload: Map[String, Any])

final case class CommanderContract(
  race: String = "Unknown",
  style: CommanderStyle = CommanderStyle(),
  activeCommands: Vector[CommanderCommand] = Vector.empty)

object CommanderIntent {
  @volatile private var contract: CommanderContract = CommanderContract()

  def current: CommanderContract = contract

  def update(next: CommanderContract): Unit = {
    contract = next
  }

  def aggressionBias: Double = current.style.aggression - 0.5
  def harassBias: Double = current.style.harass - 0.5
  def economyBias: Double = current.style.economyGreed - 0.5
  def defensiveBias: Double = current.style.defensiveSafety - 0.5

  def hasPlan(plan: String): Boolean =
    current.activeCommands.exists(c => c.payload.get("plan").contains(plan))

  def hasHardGoal(action: String): Boolean =
    current.activeCommands.exists(c => c.commandType == "hard_goal" && c.action == action)
}
