package Commander

import java.nio.charset.StandardCharsets
import java.nio.file.{Files, Path, Paths}
import scala.collection.JavaConverters._
import scala.util.parsing.json.JSON

object CommanderQueueConsumer {
  private var lastBytes: Long = -1L

  def poll(pathString: String = "runtime/commands.jsonl"): Unit = {
    val path = Paths.get(pathString)
    if (!Files.exists(path)) return
    val bytes = Files.size(path)
    if (bytes == lastBytes) return
    lastBytes = bytes

    val commands = Files
      .readAllLines(path, StandardCharsets.UTF_8)
      .asScala
      .flatMap(parseCommand)
      .toVector

    if (commands.nonEmpty) {
      CommanderIntent.update(applyCommands(CommanderIntent.current, commands))
      CommanderTelemetry.commandStatus(commands.map(_.id), "active", "accepted by PurpleWave queue consumer")
    }
  }

  private def parseCommand(line: String): Option[CommanderCommand] = {
    JSON.parseFull(line).collect { case obj: Map[String @unchecked, Any @unchecked] =>
      CommanderCommand(
        id = obj.get("command_id").map(_.toString).getOrElse("unknown"),
        commandType = obj.get("command_type").map(_.toString).getOrElse("unknown"),
        action = obj.get("action").map(_.toString).getOrElse("unknown"),
        payload = obj.get("payload").collect { case payload: Map[String @unchecked, Any @unchecked] => payload }.getOrElse(Map.empty))
    }
  }

  private def applyCommands(contract: CommanderContract, commands: Vector[CommanderCommand]): CommanderContract = {
    commands.foldLeft(contract) { (next, command) =>
      command.action match {
        case "set_race" =>
          next.copy(race = command.payload.get("race").map(_.toString).getOrElse(next.race), activeCommands = upsert(next.activeCommands, command))
        case "set_style" =>
          next.copy(style = mergeStyle(next.style, command.payload), activeCommands = upsert(next.activeCommands, command))
        case _ =>
          next.copy(activeCommands = upsert(next.activeCommands, command))
      }
    }
  }

  private def upsert(commands: Vector[CommanderCommand], command: CommanderCommand): Vector[CommanderCommand] =
    commands.filterNot(_.id == command.id) :+ command

  private def mergeStyle(style: CommanderStyle, payload: Map[String, Any]): CommanderStyle = {
    val stylePayload = payload.get("style").collect { case data: Map[String @unchecked, Any @unchecked] => data }.getOrElse(Map.empty)
    def number(key: String, fallback: Double): Double = stylePayload.get(key).map(_.toString.toDouble).getOrElse(fallback)
    style.copy(
      aggression = number("aggression", style.aggression),
      harass = number("harass", style.harass),
      economyGreed = number("economy_greed", style.economyGreed),
      defensiveSafety = number("defensive_safety", style.defensiveSafety),
      allInCommitment = number("all_in_commitment", style.allInCommitment))
  }
}
