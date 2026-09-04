import type { ChunkMember } from "@/lib/types";

type Props = {
  members: ChunkMember[];
  membersOmitted?: number | null;
};

function formatKind(value: string): string {
  return value.replaceAll("_", " ");
}

export function ChunkMembers({ members, membersOmitted = 0 }: Props) {
  const primary = members.find((member) => member.role === "primary");
  const support = members.filter((member) => member.role === "support");

  return (
    <div>
      <p className="text-sm font-medium text-slate-900">
        {primary?.statement ?? members[0]?.statement}
      </p>
      {support.length > 0 ? (
        <ul className="mt-3 space-y-2 border-l-2 border-slate-200 pl-3">
          {support.map((member) => (
            <li key={member.memory_key}>
              <p className="text-[10px] font-semibold uppercase tracking-wide text-slate-500">
                Support · {formatKind(member.memory_kind)}
              </p>
              <p className="mt-0.5 text-sm text-slate-700">{member.statement}</p>
            </li>
          ))}
        </ul>
      ) : null}
      {membersOmitted != null && membersOmitted > 0 ? (
        <p className="mt-2 text-xs text-slate-500">
          {membersOmitted} member{membersOmitted === 1 ? "" : "s"} omitted
        </p>
      ) : null}
    </div>
  );
}

export function chunkKindLabel(chunkKind: string | null | undefined, fallback: string): string {
  return formatKind(chunkKind ?? fallback);
}
