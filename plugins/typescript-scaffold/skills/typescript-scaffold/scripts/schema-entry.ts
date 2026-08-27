import { writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { z } from "zod";
import { profileSchema } from "../src/schema.js";

const schemaPath = fileURLToPath(new URL("../config/schema.json", import.meta.url));
const schema = z.toJSONSchema(profileSchema, { target: "draft-7" });
await writeFile(schemaPath, `${JSON.stringify(schema, null, 2)}\n`);
