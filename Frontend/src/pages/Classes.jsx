import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  GraduationCap, Plus, Users, UserCheck, Clock, Link2, Copy, Check, Trash2,
} from "lucide-react";
import { Card, Button, Badge, Field, Empty, stagger, riseIn } from "../components/ui";
import { getClasses, createClass, deleteClass } from "../utils/api";

/**
 * A teacher takes several classes. The flat "students" list the prototype had cannot
 * express that: roll 12 in IT-B is not roll 12 in CSE-A, and attendance for one is not
 * attendance for the other. Everything below is scoped to a class.
 */
export default function Classes() {
  const [classes, setClasses] = useState([]);
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(null);

  const load = () => getClasses().then(setClasses).catch(console.error);
  useEffect(() => { load(); }, []);

  const create = async () => {
    if (!name.trim()) return;
    setBusy(true);
    try {
      await createClass(name.trim());
      setName("");
      load();
    } catch (e) { alert(e.message); }
    setBusy(false);
  };

  const enrolLink = (code) => `${window.location.origin}/enroll/${code}`;

  const copy = (code) => {
    navigator.clipboard.writeText(enrolLink(code));
    setCopied(code);
    setTimeout(() => setCopied(null), 1600);
  };

  const remove = async (c) => {
    if (!confirm(`Delete "${c.name}"? The roster and its attendance history stay on disk, but the class disappears from here.`)) return;
    await deleteClass(c.id);
    load();
  };

  return (
    <div className="min-h-screen w-full mx-auto max-w-6xl px-4 pt-20 pb-12 sm:px-6 sm:pt-24 sm:pb-16 lg:px-8">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="display-lg text-white">My <span className="text-[--brand]">Classes</span></h1>
          <p className="mt-1.5 text-sm text-[--muted]">
            Publish a roster, share the link, students enrol themselves.
          </p>
        </div>
      </div>

      {/* create */}
      <Card pad="p-4" className="mb-5">
        <div className="flex flex-wrap items-end gap-3">
          <div className="min-w-[240px] flex-1">
            <Field
              label="New class"
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && create()}
              placeholder="e.g. IT-B 4th Year"
            />
          </div>
          <Button onClick={create} disabled={busy || !name.trim()}>
            <Plus className="h-4 w-4" /> Create class
          </Button>
        </div>
      </Card>

      {classes.length === 0 ? (
        <Card pad="p-6">
          <Empty
            icon={GraduationCap}
            title="No classes yet"
            sub="Create one above. Then add the roll numbers, and share the enrolment link with your students."
          />
        </Card>
      ) : (
        <motion.div
          variants={stagger} initial="hidden" animate="show"
          className="grid gap-4 md:grid-cols-2"
        >
          {classes.map((c) => (
            <motion.div key={c.id} variants={riseIn}>
              <Card hover pad="p-5">
                <div className="mb-4 flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <Link to={`/classes/${c.id}`}
                          className="truncate text-base font-semibold text-white hover:text-[--brand]">
                      {c.name}
                    </Link>
                    <p className="mt-0.5 text-[11px] text-slate-600">Created {c.created?.slice(0, 10)}</p>
                  </div>
                  <button
                    onClick={() => remove(c)}
                    className="shrink-0 rounded-lg border border-white/10 p-1.5 text-slate-600
                               transition hover:border-rose-400/40 hover:text-rose-400"
                    title="Delete class"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>

                {/* roster progress — the number a teacher actually checks */}
                <div className="mb-4 grid grid-cols-3 gap-2 text-center">
                  {[
                    [Users, "On roster", c.total, "text-slate-200"],
                    [UserCheck, "Enrolled", c.enrolled, "text-emerald-300"],
                    [Clock, "Pending", c.pending, c.pending ? "text-amber-300" : "text-slate-500"],
                  ].map(([Icon, label, val, tone]) => (
                    <div key={label} className="rounded-lg border border-white/10 bg-black/20 p-2.5">
                      <Icon className="mx-auto mb-1 h-3.5 w-3.5 text-slate-600" />
                      <div className={`text-base font-bold tabular-nums ${tone}`}>{val}</div>
                      <div className="text-[10px] uppercase tracking-wide text-slate-600">{label}</div>
                    </div>
                  ))}
                </div>

                {/* the shareable link */}
                <div className="mb-3 flex items-center gap-2 rounded-lg border border-white/10 bg-black/25 p-2">
                  <Link2 className="h-3.5 w-3.5 shrink-0 text-[--brand]" />
                  <code className="min-w-0 flex-1 truncate font-mono text-[11px] text-slate-400">
                    /enroll/{c.code}
                  </code>
                  <button
                    onClick={() => copy(c.code)}
                    className="shrink-0 rounded-md border border-white/12 px-2 py-1 text-[10px]
                               font-medium text-slate-300 transition hover:border-[--brand] hover:text-white"
                  >
                    {copied === c.code
                      ? <span className="flex items-center gap-1 text-emerald-400"><Check className="h-3 w-3" />Copied</span>
                      : <span className="flex items-center gap-1"><Copy className="h-3 w-3" />Copy</span>}
                  </button>
                </div>

                <Button as={Link} to={`/classes/${c.id}`} variant="ghost" size="sm" className="mt-auto w-full">
                  Open class
                </Button>
              </Card>
            </motion.div>
          ))}
        </motion.div>
      )}

      <p className="mt-6 text-center text-[11px] text-slate-600">
        Only roll numbers you add to a roster can enrol through the link — sharing it in a
        group chat does not let outsiders add themselves.
      </p>
    </div>
  );
}
