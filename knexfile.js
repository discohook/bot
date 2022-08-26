const { config } = require("dotenv-cra")

process.env.NODE_ENV ??= "development"
config()

/** @type {import("knex").Knex.Config} */
module.exports = {
  client: "pg",
  connection: process.env.DATABASE_URL,
  pool: {
    min: 0,
    max: 16,
  },
}
