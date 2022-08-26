import knex from "knex"

export const createDatabaseConnection = () =>
  knex(require("../../../knexfile.js"))
