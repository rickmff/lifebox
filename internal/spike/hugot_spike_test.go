package spike

import (
	"context"
	"math"
	"os"
	"strings"
	"testing"
	"time"

	"github.com/knights-analytics/hugot"
	"github.com/knights-analytics/hugot/pipelines"
)

func cosine(a, b []float32) float64 {
	var dot, na, nb float64
	for i := range a {
		dot += float64(a[i]) * float64(b[i])
		na += float64(a[i]) * float64(a[i])
		nb += float64(b[i]) * float64(b[i])
	}
	return dot / (math.Sqrt(na) * math.Sqrt(nb))
}

func TestHugotGoBackend(t *testing.T) {
	model := os.Getenv("LIFEBOX_SPIKE_MODEL")
	if model == "" {
		t.Skip("set LIFEBOX_SPIKE_MODEL=intfloat/multilingual-e5-small to run")
	}
	ctx := context.Background()
	dir := "/root/.cache/lifebox/models"
	if err := os.MkdirAll(dir, 0o755); err != nil {
		t.Fatal(err)
	}
	opts := hugot.NewDownloadOptions()
	opts.Verbose = true
	if p := os.Getenv("LIFEBOX_SPIKE_ONNX"); p != "" {
		opts.OnnxFilePath = p
	}
	start := time.Now()
	modelPath, err := hugot.DownloadModel(ctx, model, dir, opts)
	if err != nil {
		t.Fatal("download:", err)
	}
	t.Logf("model at %s (download/validate took %s)", modelPath, time.Since(start))

	start = time.Now()
	session, err := hugot.NewGoSession(ctx)
	if err != nil {
		t.Fatal("session:", err)
	}
	defer session.Destroy()

	cfg := hugot.FeatureExtractionConfig{
		ModelPath: modelPath,
		Name:      "embed",
		Options:   []hugot.FeatureExtractionOption{pipelines.WithNormalization()},
	}
	if p := os.Getenv("LIFEBOX_SPIKE_ONNX_FILE"); p != "" {
		cfg.OnnxFilename = p
	}
	pipe, err := hugot.NewPipeline(session, cfg)
	if err != nil {
		t.Fatal("pipeline:", err)
	}
	t.Logf("pipeline ready in %s", time.Since(start))

	texts := []string{
		"query: passaporte brasileiro",
		"passage: Passaporte da República Federativa do Brasil, documento de viagem válido até 2030",
		"passage: Fatura de eletricidade da EDP referente ao mês de março, valor 45 euros",
		"passage: Título de residência emitido pela AIMA, autorização de residência temporária",
	}
	start = time.Now()
	out, err := pipe.RunPipeline(ctx, texts)
	if err != nil {
		t.Fatal("run:", err)
	}
	t.Logf("embedded %d texts in %s, dims=%d", len(texts), time.Since(start), len(out.Embeddings[0]))
	q := out.Embeddings[0]
	for i := 1; i < len(texts); i++ {
		t.Logf("cos(query, %q) = %.4f", texts[i][:40], cosine(q, out.Embeddings[i]))
	}
	if cosine(q, out.Embeddings[1]) <= cosine(q, out.Embeddings[2]) {
		t.Fatalf("passport passage should rank above invoice")
	}

	// throughput: 16 chunks of ~800 chars
	chunk := strings.Repeat("Comprovativo de morada emitido pela Junta de Freguesia de Lisboa, atestado de residência para efeitos de renovação de autorização de residência. ", 6)
	batch := make([]string, 16)
	for i := range batch {
		batch[i] = "passage: " + chunk
	}
	start = time.Now()
	if _, err := pipe.RunPipeline(ctx, batch); err != nil {
		t.Fatal(err)
	}
	t.Logf("batch of 16 x %d chars: %s", len(chunk), time.Since(start))
	start = time.Now()
	if _, err := pipe.RunPipeline(ctx, []string{"query: renovação de autorização de residência"}); err != nil {
		t.Fatal(err)
	}
	t.Logf("single query embed: %s", time.Since(start))
}
