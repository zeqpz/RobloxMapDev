export const meta = {
  name: 'build-building',
  description: 'Plan, model in Blender, audit to the R6 standard, texture, export and import one Southwest building',
  whenToUse: 'Run with args {slug, description} when the owner describes a new building for the Roblox map. Needs Blender open with MCP for Blender; Studio open for the import phase.',
  phases: [
    { title: 'Plan', detail: 'references + map-architect construction plan' },
    { title: 'Model', detail: 'blender-builder in the live Blender' },
    { title: 'Audit', detail: 'standards-auditor, fix loop (max 3 rounds)' },
    { title: 'Texture', detail: 'texture-artist PBR materials' },
    { title: 'Export + import', detail: 'FBX export, Studio import, ScaleAudit' },
  ],
}

// args: { slug: "abq_flat_roof_house_a", description: "<owner's building description, verbatim>",
//         skipImport?: true }
const slug = args && args.slug
const description = args && args.description
if (!slug || !description) throw new Error('pass args {slug, description}')

const AUDIT = {
  type: 'object',
  properties: {
    pass: { type: 'boolean' },
    issues: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          severity: { type: 'string', enum: ['high', 'medium', 'low'] },
          item: { type: 'string' }, measured: { type: 'string' }, expected: { type: 'string' }, fix: { type: 'string' },
        },
        required: ['severity', 'item', 'fix'],
      },
    },
  },
  required: ['pass', 'issues'],
}

// ---------------------------------------------------------------- Plan
phase('Plan')
const refs = await agent(
  `Find 4-8 reference images for this building from research/city-reference (and capture new ones only if nothing ` +
  `fits). Building "${slug}": ${description}. Return image paths with one line each on what to copy.`,
  { label: 'references', phase: 'Plan', agentType: 'reference-researcher' })
const plan = await agent(
  `Write the construction plan plans/${slug}.md for this building, following your section format exactly.\n` +
  `Owner's description (verbatim): ${description}\n\nReference images found:\n${refs}`,
  { label: 'plan', phase: 'Plan', agentType: 'map-architect' })
log(`plan written: plans/${slug}.md`)

// ---------------------------------------------------------------- Model (single live Blender -> strictly sequential)
phase('Model')
let build = await agent(
  `Build "${slug}" in the live Blender from plans/${slug}.md. Save blender/scenes/${slug}.blend. Do not export yet.\n` +
  `Planner summary:\n${plan}`,
  { label: 'model', phase: 'Model', agentType: 'blender-builder' })

// ---------------------------------------------------------------- Audit + fix loop
phase('Audit')
let audit = null
for (let round = 1; round <= 3; round++) {
  audit = await agent(
    `Audit "${slug}" in Blender (collection "${slug}") against plans/${slug}.md, standards/sizes.json and the plan's ` +
    `reference images. Round ${round}. Measure everything you report.`,
    { label: `audit r${round}`, phase: 'Audit', agentType: 'standards-auditor', schema: AUDIT })
  const blocking = (audit && audit.issues || []).filter(i => i.severity !== 'low')
  log(`audit round ${round}: ${blocking.length} high/medium issue(s)`)
  if (audit && audit.pass && !blocking.length) break
  if (round === 3) { log('still failing after 3 rounds - stopping before texturing'); return { slug, plan, build, audit } }
  build = await agent(
    `Fix these audit findings on "${slug}" in the live Blender, then save the .blend:\n` +
    JSON.stringify(blocking, null, 1),
    { label: `fix r${round}`, phase: 'Audit', agentType: 'blender-builder' })
}

// ---------------------------------------------------------------- Texture
phase('Texture')
const textures = await agent(
  `Make and assign the materials for "${slug}" per the material plan in plans/${slug}.md (Blender collection "${slug}"). ` +
  `Save the .blend.`,
  { label: 'textures', phase: 'Texture', agentType: 'texture-artist' })

// ---------------------------------------------------------------- Export + import
phase('Export + import')
const exported = await agent(
  `Export "${slug}" with rmd_kit.export_fbx to exports/${slug}/${slug}.fbx (root objects of collection "${slug}", ` +
  `no reference objects). Report the object list, triangle totals and the path.`,
  { label: 'export', phase: 'Export + import', agentType: 'blender-builder' })
let imported = 'skipped (skipImport)'
let finalAudit = null
if (!args.skipImport) {
  imported = await agent(
    `Bring exports/${slug}/${slug}.fbx into the RobloxMapDev Studio place per your rules (ask the user for the 3D ` +
    `Importer step if needed), set properties, hook up textures from textures/roblox/${slug}/, run ScaleAudit.`,
    { label: 'import', phase: 'Export + import', agentType: 'roblox-importer' })
  finalAudit = await agent(
    `Audit the imported Model for "${slug}" in Roblox Studio (scale, R6 fit, Roblox settings, budgets).`,
    { label: 'studio audit', phase: 'Export + import', agentType: 'standards-auditor', schema: AUDIT })
}
return { slug, plan, audit, textures, exported, imported, finalAudit }
