package spike

import (
	"encoding/binary"
	"math"
	"testing"

	"github.com/ncruces/go-sqlite3"
	"github.com/ncruces/go-sqlite3/ext/fts5"
	"github.com/ncruces/go-sqlite3/ext/vec1"
)

func f32blob(v []float32) []byte {
	b := make([]byte, 4*len(v))
	for i, x := range v {
		binary.LittleEndian.PutUint32(b[4*i:], math.Float32bits(x))
	}
	return b
}

func TestVec1AndFTS5(t *testing.T) {
	db, err := sqlite3.Open(":memory:")
	if err != nil {
		t.Fatal(err)
	}
	defer db.Close()
	if err := vec1.Register(db); err != nil {
		t.Fatal("vec1:", err)
	}
	if err := fts5.Register(db); err != nil {
		t.Fatal("fts5:", err)
	}

	stmt, _, err := db.Prepare(`SELECT sqlite_version(), vec1_info()`)
	if err != nil {
		t.Fatal(err)
	}
	if stmt.Step() {
		t.Logf("sqlite %s, vec1 %s", stmt.ColumnText(0), stmt.ColumnText(1))
	}
	stmt.Close()

	err = db.Exec(`
		CREATE VIRTUAL TABLE v USING vec1(vector, document_id);
		INSERT INTO v(cmd, arg) VALUES('rebuild', '{index:"flat", distance:"cos"}');
	`)
	if err != nil {
		t.Fatal("create vec1:", err)
	}

	ins, _, err := db.Prepare(`INSERT INTO v(rowid, vector, document_id) VALUES(?, ?, ?)`)
	if err != nil {
		t.Fatal(err)
	}
	vectors := map[int64][]float32{
		1: {1, 0, 0, 0},
		2: {0.9, 0.1, 0, 0},
		3: {0, 0, 1, 0},
		4: {0, 0, 0.8, 0.2},
	}
	for id, vec := range vectors {
		ins.BindInt64(1, id)
		ins.BindBlob(2, f32blob(vec))
		ins.BindInt64(3, id*10)
		if err := ins.Exec(); err != nil {
			t.Fatal("insert:", err)
		}
	}
	ins.Close()

	q, _, err := db.Prepare(`SELECT rowid, document_id, distance FROM v(?, '{K: 2}')`)
	if err != nil {
		t.Fatal("knn prepare:", err)
	}
	q.BindBlob(1, f32blob([]float32{1, 0.05, 0, 0}))
	var got []int64
	for q.Step() {
		got = append(got, q.ColumnInt64(0))
		t.Logf("knn rowid=%d doc=%d distance=%f", q.ColumnInt64(0), q.ColumnInt64(1), q.ColumnFloat(2))
	}
	if err := q.Err(); err != nil {
		t.Fatal("knn:", err)
	}
	q.Close()
	if len(got) != 2 || got[0] != 1 || got[1] != 2 {
		t.Fatalf("unexpected knn order: %v", got)
	}

	// scalar distance + json helpers
	d, _, err := db.Prepare(`SELECT vec1_cos_distance(vec1_from_json('[1,0,0,0]'), ?), vec1_to_json(?)`)
	if err != nil {
		t.Fatal(err)
	}
	d.BindBlob(1, f32blob([]float32{0, 1, 0, 0}))
	d.BindBlob(2, f32blob([]float32{0.5, 0.25, 0, 0}))
	if d.Step() {
		t.Logf("cos distance orthogonal=%f json=%s", d.ColumnFloat(0), d.ColumnText(1))
		if math.Abs(d.ColumnFloat(0)-1.0) > 1e-5 {
			t.Fatalf("expected distance 1.0, got %f", d.ColumnFloat(0))
		}
	}
	d.Close()

	// delete + count
	if err := db.Exec(`DELETE FROM v WHERE rowid = 3`); err != nil {
		t.Fatal("delete:", err)
	}
	c, _, _ := db.Prepare(`SELECT count(*) FROM v`)
	if c.Step() {
		t.Logf("count after delete=%d", c.ColumnInt(0))
	}
	c.Close()

	// FTS5 external-content table with diacritics removal
	err = db.Exec(`
		CREATE TABLE docs(id INTEGER PRIMARY KEY, title TEXT, body TEXT);
		CREATE VIRTUAL TABLE docs_fts USING fts5(title, body, content='docs', content_rowid='id', tokenize='unicode61 remove_diacritics 2');
		CREATE TRIGGER docs_ai AFTER INSERT ON docs BEGIN
		  INSERT INTO docs_fts(rowid, title, body) VALUES (new.id, new.title, new.body);
		END;
		INSERT INTO docs(title, body) VALUES ('Título de Residência', 'Autorização de residência emitida pela AIMA, válida até 2027');
		INSERT INTO docs(title, body) VALUES ('Fatura EDP', 'Eletricidade março');
	`)
	if err != nil {
		t.Fatal("fts5 setup:", err)
	}
	f, _, err := db.Prepare(`SELECT rowid, bm25(docs_fts, 2.0, 1.0), snippet(docs_fts, 1, '[', ']', '…', 8) FROM docs_fts WHERE docs_fts MATCH ? ORDER BY bm25(docs_fts, 2.0, 1.0)`)
	if err != nil {
		t.Fatal(err)
	}
	f.BindText(1, `"titulo" OR "residenc"*`)
	n := 0
	for f.Step() {
		n++
		t.Logf("fts rowid=%d score=%f snippet=%q", f.ColumnInt64(0), f.ColumnFloat(1), f.ColumnText(2))
	}
	f.Close()
	if n != 1 {
		t.Fatalf("expected 1 fts hit, got %d", n)
	}
}
