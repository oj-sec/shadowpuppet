import { LabelRenderer, LabelOptions } from '@interacta/css-labels';
import type { Graph } from '@cosmos.gl/graph';

export class CosmosLabels {
    private labelRenderer: LabelRenderer;
    private labels: LabelOptions[] = [];
    private pointIndexToLabel: Map<number, string>;

    constructor(div: HTMLDivElement, pointIndexToLabel: Map<number, string>) {
        this.labelRenderer = new LabelRenderer(div, { pointerEvents: 'none' });
        this.pointIndexToLabel = pointIndexToLabel;
    }

    update(graph: Graph): void {
        const trackedNodesPositions = graph.getTrackedPointPositionsMap();
        let index = 0;
        trackedNodesPositions.forEach((positions, pointIndex) => {
            const screenPosition = graph.spaceToScreenPosition([
                positions?.[0] ?? 0,
                positions?.[1] ?? 0,
            ]);
            const radius = graph.spaceToScreenRadius(
                graph.getPointRadiusByIndex(pointIndex) as number
            );
            this.labels[index] = {
                id: `${pointIndex}`,
                text: this.pointIndexToLabel.get(pointIndex) ?? '',
                x: screenPosition[0],
                y: screenPosition[1] - (radius + 2),
                opacity: 1,
            };
            index += 1;
        });
        this.labelRenderer.setLabels(this.labels);
        this.labelRenderer.draw(true);
    }
}
