package spike

import (
	"bytes"
	"fmt"
	"image/png"
	"strings"
	"testing"
	"time"

	"github.com/klippa-app/go-pdfium/requests"
	"github.com/klippa-app/go-pdfium/webassembly"
)

func minimalPDF(text string) []byte {
	var b bytes.Buffer
	var offsets []int
	obj := func(s string) {
		offsets = append(offsets, b.Len())
		b.WriteString(s)
	}
	b.WriteString("%PDF-1.4\n")
	obj("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
	obj("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
	obj("3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n")
	content := fmt.Sprintf("BT /F1 24 Tf 72 720 Td (%s) Tj ET", text)
	obj(fmt.Sprintf("4 0 obj\n<< /Length %d >>\nstream\n%s\nendstream\nendobj\n", len(content), content))
	obj("5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")
	xref := b.Len()
	fmt.Fprintf(&b, "xref\n0 %d\n0000000000 65535 f \n", len(offsets)+1)
	for _, o := range offsets {
		fmt.Fprintf(&b, "%010d 00000 n \n", o)
	}
	fmt.Fprintf(&b, "trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n", len(offsets)+1, xref)
	return b.Bytes()
}

func TestPdfiumWasm(t *testing.T) {
	start := time.Now()
	pool, err := webassembly.Init(webassembly.Config{MinIdle: 1, MaxIdle: 1, MaxTotal: 2})
	if err != nil {
		t.Fatal(err)
	}
	defer pool.Close()
	t.Logf("pool init: %s", time.Since(start))

	inst, err := pool.GetInstance(30 * time.Second)
	if err != nil {
		t.Fatal(err)
	}
	defer inst.Close()

	pdf := minimalPDF("Titulo de Residencia Lifebox 2026")
	doc, err := inst.OpenDocument(&requests.OpenDocument{File: &pdf})
	if err != nil {
		t.Fatal("open:", err)
	}
	defer inst.FPDF_CloseDocument(&requests.FPDF_CloseDocument{Document: doc.Document})

	pc, err := inst.FPDF_GetPageCount(&requests.FPDF_GetPageCount{Document: doc.Document})
	if err != nil {
		t.Fatal(err)
	}
	t.Logf("pages: %d", pc.PageCount)

	page := requests.Page{ByIndex: &requests.PageByIndex{Document: doc.Document, Index: 0}}
	txt, err := inst.GetPageText(&requests.GetPageText{Page: page})
	if err != nil {
		t.Fatal("text:", err)
	}
	t.Logf("text: %q", txt.Text)
	if !strings.Contains(txt.Text, "Residencia") {
		t.Fatalf("text layer not extracted: %q", txt.Text)
	}

	rs := time.Now()
	render, err := inst.RenderPageInDPI(&requests.RenderPageInDPI{Page: page, DPI: 110})
	if err != nil {
		t.Fatal("render:", err)
	}
	defer render.Cleanup()
	var out bytes.Buffer
	if err := png.Encode(&out, render.Result.RenderedImage); err != nil {
		t.Fatal(err)
	}
	t.Logf("render %dx%d in %s, png %d bytes", render.Result.Width, render.Result.Height, time.Since(rs), out.Len())
}
