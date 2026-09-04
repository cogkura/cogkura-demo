import type { AssociationPath, MemoryItem } from "@/lib/types";

import { ChunkMembers, chunkKindLabel } from "./chunk-members";

type Props = {
  item: MemoryItem;
  showDetails?: boolean;
};

function RelationshipPathSummary({ path }: { path: AssociationPath }) {
  if (path.hop_kind !== "relationship" || path.relationship_edges.length === 0) {
    return null;
  }
  const seed = path.seed_entity_id ?? path.seed_episode_id ?? "query";
  return (
    <div>
      <dt className="font-medium">Structured path</dt>
      <dd className="font-mono">
        {seed}
        {path.relationship_edges.map((edge) => (
          <span key={edge.relationship_id}>
            {" "}
            ← {edge.relation_type} {edge.target_entity_id}
          </span>
        ))}
      </dd>
    </div>
  );
}

export function MemoryItemCard({ item, showDetails = false }: Props) {
  const members = item.members ?? [];
  const kindLabel = chunkKindLabel(item.chunk_kind, item.memory_kind);
  const memberCount = item.member_count ?? members.length;

  return (
    <article className="rounded-xl border border-slate-200 bg-slate-50 p-4">
      {members.length > 0 ? (
        <ChunkMembers members={members} membersOmitted={item.members_omitted} />
      ) : (
        <p className="text-sm font-medium text-slate-900">{item.statement}</p>
      )}
      <p className="mt-2 text-xs uppercase tracking-wide text-slate-500">
        {kindLabel}
        {item.chunk_kind && memberCount > 0 ? ` · ${memberCount} members` : ""}
      </p>
      {showDetails ? (
        <dl className="mt-3 grid gap-2 text-xs text-slate-600">
          {item.score !== null ? (
            <div>
              <dt className="inline font-medium">Score: </dt>
              <dd className="inline">{item.score.toFixed(3)}</dd>
            </div>
          ) : null}
          {item.activation !== null ? (
            <div>
              <dt className="inline font-medium">Activation: </dt>
              <dd className="inline">{item.activation.toFixed(3)}</dd>
            </div>
          ) : null}
          {item.retrieval_reason ? (
            <div>
              <dt className="font-medium">Retrieval</dt>
              <dd>{item.retrieval_reason}</dd>
            </div>
          ) : null}
          {item.association_path ? (
            <RelationshipPathSummary path={item.association_path} />
          ) : null}
          {item.selection_reason ? (
            <div>
              <dt className="font-medium">Selection</dt>
              <dd>{item.selection_reason}</dd>
            </div>
          ) : null}
          {item.learned_utility !== null && item.learned_utility !== undefined ? (
            <div>
              <dt className="inline font-medium">Learned utility: </dt>
              <dd className="inline">{item.learned_utility.toFixed(3)}</dd>
            </div>
          ) : null}
        </dl>
      ) : null}
    </article>
  );
}
