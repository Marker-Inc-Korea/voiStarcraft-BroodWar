package Commander

import java.nio.charset.StandardCharsets
import java.nio.file.{Files, Paths, StandardOpenOption}

object CommanderTelemetry {
  private val path = Paths.get("runtime/telemetry.jsonl")

  def commandStatus(commandIds: Seq[String], status: String, reason: String): Unit = {
    commandIds.foreach { id =>
      write(s"""{"event_type":"command_status","payload":{"command_id":"$id","status":"$status","reason":"$reason"}}""")
    }
  }

  def intentAdherence(score: Double): Unit = {
    write(s"""{"event_type":"intent_adherence","payload":{"score":$score}}""")
  }

  private def write(line: String): Unit = {
    Files.createDirectories(path.getParent)
    Files.write(
      path,
      (line + System.lineSeparator()).getBytes(StandardCharsets.UTF_8),
      StandardOpenOption.CREATE,
      StandardOpenOption.APPEND)
  }
}
