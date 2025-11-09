import { LabelRenderer } from '@interacta/css-labels';
import type { LabelOptions } from '@interacta/css-labels';
import type { Graph } from '@cosmos.gl/graph';

export class CosmosLabels {
    private labelRenderer: LabelRenderer;
    private labels: LabelOptions[] = [];
    public pointIndexToLabel: Map<number, string>;

    constructor(div: HTMLDivElement, pointIndexToLabel: Map<number, string>) {
        this.labelRenderer = new LabelRenderer(div, { pointerEvents: 'none' });
        this.pointIndexToLabel = pointIndexToLabel;
    }

    update(graph: Graph): void {
        const trackedNodesPositions = graph.getTrackedPointPositionsMap();
        let index = 0;

        trackedNodesPositions.forEach((positions, pointIndex) => {
            if (!positions) return;

            const screenPosition = graph.spaceToScreenPosition([
                positions[0],
                positions[1],
            ]);

            const radius = graph.spaceToScreenRadius(
                graph.getPointRadiusByIndex(pointIndex) as number
            );

            this.labels[index] = {
                id: `${pointIndex}`,
                text: this.pointIndexToLabel.get(pointIndex) ?? '',
                x: screenPosition[0],
                y: screenPosition[1] - (radius),
                opacity: 0.5,
                style: "p-2",
            };
            index += 1;
        });

        this.labelRenderer.setLabels(this.labels);
        this.labelRenderer.draw(true);
    }

    destroy(): void {
        this.labelRenderer.destroy();
        this.labels = [];
    }
}